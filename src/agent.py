import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date

from src.config import REFERENCE_DATE
from src.calendar_util import (
    parse_date,
    add_business_days,
    add_calendar_days,
    format_date_for_chat,
    format_date_for_speech,
    REF_DATE,
)
from src.retriever import HybridRetriever
from src.tools_adapter import SupportTools
from src.llm_client import GeminiClient


SYSTEM_INSTRUCTION_STEP1 = """You are ZentroMart's customer support assistant.
Follow these rules:
1. In your first reply, identify yourself clearly as ZentroMart's AI support assistant.
2. Maintain a polite and helpful tone.
3. Answer the customer's question directly based on general e-commerce assumptions.
"""

SYSTEM_INSTRUCTION_STEP2 = """You are ZentroMart's official AI customer support assistant.
ZentroMart is an Indian online store selling groceries, fashion, electronics, and home items.
Today's date is frozen at 20 October 2026.

STRICT GROUNDING RULES:
1. First reply requirement: Introduce yourself as ZentroMart's AI support assistant.
2. Reply in 2 to 3 short sentences. Match the customer's language (English, Hindi, or Hinglish).
3. Ground your answer ONLY on the provided context sections.
4. If the context does not contain the answer, say politely:
   "Sorry, I don't have information about that. I can connect you to a colleague who can help." (or in Hindi: "माफ़ कीजिए, मेरे पास इस बारे में जानकारी नहीं है। मैं आपको एक सहयोगी से कनेक्ट कर सकती हूँ।")
   NEVER invent, guess, or extrapolate dates, policies, discounts, or terms not explicitly in the context.
5. Follow document precedence: Current Policy > Agent Guide > Help > FAQ > Marketing. If an FAQ contradicts a Policy, Policy always wins.
6. When calculating dates, remember:
   - Reference date is 20 October 2026.
   - Business days: Monday through Saturday (excluding warehouse holidays: 15 Aug 2026, 2 Oct 2026, 19 Oct 2026, 9 Nov 2026).
   - Return windows: calendar days from delivery date.
"""

SYSTEM_INSTRUCTION_STEP3 = """You are ZentroMart's AI customer support assistant.
Today's reference date is 20 October 2026.

RULES FOR MULTI-TURN CONVERSATION:
1. Always introduce yourself as ZentroMart's AI assistant in your very first reply.
2. Identity Verification:
   - For order-specific requests, order ID is required first.
   - Once order ID is given, ask the caller for ONE verification factor: the last 4 digits of their registered phone number OR their 6-digit delivery pincode.
   - NEVER disclose order status, items, amounts, or address before verification succeeds.
   - NEVER read out the customer's phone number, email, or address.
3. Escalation & Handover:
   - When a ticket is created for escalation, inform the customer politely that a ticket has been created and a human colleague will assist them.
   - Escalation reasons: Customer asks for human, damaged/defective item > ₹10,000, repeat contacts >= 2, product safety issues, or unreasonable compensation demands.
   - Politely refuse policy violations (e.g. cash compensation not covered by policy) and escalate to human.
4. Keep replies to 2-3 short, clear sentences. Speak in the customer's chosen language.
"""


class SupportAgent:
    def __init__(self, mode: str = "step3"):
        self.mode = mode
        self.retriever = HybridRetriever()
        self.llm = GeminiClient()
        self.tools = SupportTools()

        # Session state
        self.reset()

    def reset(self):
        self.history: List[Dict[str, str]] = []
        self.order_id: Optional[str] = None
        self.is_verified: bool = False
        self.verification_attempts: int = 0
        self.order_data: Optional[Dict[str, Any]] = None
        self.active_sku: Optional[str] = None
        self.turn_count: int = 0

    def _normalize_speech_digits(self, text: str) -> str:
        word_map = {
            "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
            "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
            "shunya": "0", "ek": "1", "do": "2", "teen": "3", "char": "4",
            "paanch": "5", "chhe": "6", "saat": "7", "aath": "8", "nau": "9",
        }
        tokens = text.lower().split()
        converted = []
        for tok in tokens:
            clean_tok = re.sub(r"\W+", "", tok)
            if clean_tok in word_map:
                converted.append(word_map[clean_tok])
            else:
                converted.append(tok)
        res = " ".join(converted)
        # Collapse consecutive spaced digits: "8 9 7 8" -> "8978"
        res = re.sub(r"(\d)\s+(\d)", r"\1\2", res)
        res = re.sub(r"(\d)\s+(\d)", r"\1\2", res)
        return res

    def _extract_order_id(self, text: str) -> Optional[str]:
        # Handle word numbers and digit patterns
        norm = self._normalize_speech_digits(text)
        m = re.search(r"\b(\d{4})\s*(\d{4})\b", norm)
        if m:
            return f"{m.group(1)}{m.group(2)}"
        m8 = re.search(r"\b(\d{8})\b", norm)
        if m8:
            return m8.group(1)
        return None

    def _extract_verification_value(self, text: str) -> Optional[str]:
        norm = self._normalize_speech_digits(text)
        clean = re.sub(r"\b(\d{4})\s*(\d{4})\b", "", norm)
        clean = re.sub(r"\b(\d{8})\b", "", clean)
        m6 = re.search(r"\b(\d{6})\b", clean)
        if m6:
            return m6.group(1)
        m4 = re.search(r"\b(\d{4})\b", clean)
        if m4:
            return m4.group(1)
        return None

    def _is_hindi(self, text: str) -> bool:
        return any("\u0900" <= c <= "\u097f" for c in text)

    def _detect_escalation_intent(self, text: str) -> bool:
        t_low = text.lower()
        triggers = [
            "human", "person", "colleague", "agent", "executive", "representative",
            "insaan", "इंसान", "बात करनी", "सहयोगी", "priority", "consumer court",
            "police", "compensation", "₹500", "500 rs", "500 rupe", "harjaana", "हर्जाना"
        ]
        return any(trig in t_low for trig in triggers)

    def respond(self, user_message: str) -> Tuple[str, List[str], Optional[Dict[str, Any]]]:
        """
        Process user message and return (reply_text, retrieved_chunk_ids, tool_calls_made).
        """
        self.turn_count += 1
        is_first_turn = self.turn_count == 1
        retrieved_tokens: List[str] = []
        tool_call_info: Optional[Dict[str, Any]] = None
        is_hi = self._is_hindi(user_message)

        # ----------------- STEP 1: Prompting Only -----------------
        if self.mode == "step1":
            prompt = f"Customer says: {user_message}\n\nPlease respond concisely as ZentroMart AI assistant."
            reply = self.llm.generate(prompt, system_instruction=SYSTEM_INSTRUCTION_STEP1)
            self.history.append({"user": user_message, "assistant": reply})
            return reply, [], None

        # ----------------- STEP 2: Grounded RAG -----------------
        if self.mode == "step2":
            retrieval_res = self.retriever.retrieve(user_message)
            retrieved_tokens = retrieval_res["evidence_tokens"]

            prompt = (
                f"KNOWLEDGE BASE CONTEXT:\n{retrieval_res['context']}\n\n"
                f"CUSTOMER QUESTION: {user_message}\n\n"
                f"Answer the customer question in 2-3 short sentences. If not covered by context, politely say you don't have information."
            )
            reply = self.llm.generate(prompt, system_instruction=SYSTEM_INSTRUCTION_STEP2)
            self.history.append({"user": user_message, "assistant": reply})
            return reply, retrieved_tokens, None

        # ----------------- STEP 3: Multi-turn Conversation & Tools -----------------
        # Check for order ID in user message
        found_order_id = self._extract_order_id(user_message)
        if found_order_id and not self.order_id:
            self.order_id = found_order_id

        # Turn 1: Initial greeting and AI intro
        if is_first_turn and not self.order_id:
            intro_tokens = ["STY-1"]
            if is_hi:
                reply = "नमस्ते! मैं ZentroMart की AI सपोर्ट असिस्टेंट हूँ। क्या आप मुझे अपना 8 अंकों का ऑर्डर नंबर बता सकते हैं ताकि मैं आपकी मदद कर सकूँ?"
            else:
                reply = "Hello! I am ZentroMart's AI support assistant. Could you please share your 8-digit order number so I can assist you?"
            self.history.append({"user": user_message, "assistant": reply})
            return reply, intro_tokens, None

        # If order ID is present but not yet verified
        if self.order_id and not self.is_verified:
            v_val = self._extract_verification_value(user_message)

            if not v_val:
                # Trigger unverified lookup
                lookup_res = self.tools.lookup_order(self.order_id)
                tool_call_info = {"tool": "lookup_order", "args": {"order_id": self.order_id}, "result": lookup_res}
                retrieved_tokens.append("IDV-2")

                if is_hi:
                    reply = "ऑर्डर की सुरक्षा के लिए, कृपया अपने रजिस्टर्ड फ़ोन नंबर के आख़िरी 4 अंक या डिलीवरी पिनकोड बता दीजिए।"
                else:
                    reply = "For security, could you please provide the last 4 digits of your registered phone number or your delivery pincode?"
                self.history.append({"user": user_message, "assistant": reply})
                return reply, retrieved_tokens, tool_call_info

            else:
                # Attempt verification
                lookup_res = self.tools.lookup_order(self.order_id, verification_value=v_val)
                tool_call_info = {
                    "tool": "lookup_order",
                    "args": {"order_id": self.order_id, "verification_value": v_val},
                    "result": lookup_res,
                }
                retrieved_tokens.append("IDV-2")

                if lookup_res.get("verified"):
                    self.is_verified = True
                    self.order_data = lookup_res
                    cust_name = lookup_res.get("customer_first_name", "")
                    if is_hi:
                        reply = f"धन्यवाद {cust_name}, आपका वेरिफिकेशन पूरा हो गया है। बताइए मैं आपके ऑर्डर {self.order_id} के बारे में क्या मदद कर सकती हूँ?"
                    else:
                        reply = f"Thank you {cust_name}, your identity has been verified. How can I help you with order {self.order_id} today?"
                    self.history.append({"user": user_message, "assistant": reply})
                    return reply, retrieved_tokens, tool_call_info
                else:
                    self.verification_attempts += 1
                    if is_hi:
                        reply = "माफ़ कीजिए, यह विवरण मेल नहीं खाता। कृपया अपने रजिस्टर्ड फ़ोन के आख़िरी 4 अंक दोबारा चेक करके बताएँ।"
                    else:
                        reply = "Sorry, that verification detail did not match. Please verify the last 4 digits of your phone number or your delivery pincode."
                    self.history.append({"user": user_message, "assistant": reply})
                    return reply, retrieved_tokens, tool_call_info

        # Verified Order Handling OR General Inquiries
        # Check for escalation triggers
        escalation_needed = self._detect_escalation_intent(user_message)
        
        # Check high-value damage or policy limits
        if self.order_data:
            items = self.order_data.get("items", [])
            for item in items:
                # High value damage check (> ₹10,000)
                unit_price = item.get("unit_price_inr", 0)
                qty = item.get("qty", 1)
                if unit_price * qty >= 10000 and any(w in user_message.lower() for w in ["damage", "broken", "kharab", "tuta"]):
                    escalation_needed = True
                    break

        if escalation_needed:
            reason = "human_handover_or_high_value"
            summary = f"Customer requested human escalation for order {self.order_id or 'N/A'}. User message: '{user_message}'. Requires specialist review."
            ticket_res = self.tools.create_ticket(
                summary=summary,
                order_id=self.order_id,
                reason=reason,
                intent="escalation",
            )
            tool_call_info = {"tool": "create_ticket", "args": {"summary": summary}, "result": ticket_res}
            retrieved_tokens.extend(["ESC-1", "ESC-2"])

            if is_hi:
                reply = f"मैंने आपकी समस्या के लिए टिकट ({ticket_res.get('ticket_id')}) दर्ज कर दिया है। हमारी प्रायोरिटी सपोर्ट टीम जल्द ही आपसे संपर्क करेगी।"
            else:
                reply = f"I have created a support ticket ({ticket_res.get('ticket_id')}) for this issue. A human specialist from our team will contact you shortly."
            self.history.append({"user": user_message, "assistant": reply})
            return reply, retrieved_tokens, tool_call_info

        # Normal RAG with Order Context
        retrieval_res = self.retriever.retrieve(user_message)
        retrieved_tokens.extend(retrieval_res["evidence_tokens"])

        order_context_str = ""
        if self.order_data:
            order_context_str = f"VERIFIED ORDER DATA:\n{self.order_data}\n"

        prompt = (
            f"REFERENCE DATE: {REFERENCE_DATE}\n"
            f"{order_context_str}"
            f"KNOWLEDGE BASE CONTEXT:\n{retrieval_res['context']}\n\n"
            f"CUSTOMER MESSAGE: {user_message}\n\n"
            f"Respond concisely in 2-3 short sentences. Strict adherence to policies and dates."
        )

        reply = self.llm.generate(prompt, system_instruction=SYSTEM_INSTRUCTION_STEP3)
        self.history.append({"user": user_message, "assistant": reply})
        return reply, retrieved_tokens, tool_call_info
