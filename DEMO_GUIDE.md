# 2-Minute Demo Video Guide (VoiceOps 2026)

This guide provides the exact script and flow for recording your **max 2-minute demo video** as requested in the Capstone Brief.

---

## 🎯 Video Objective
Demonstrate:
1. A question answered directly from the company documents.
2. A contextual follow-up question (remembering the order and item).
3. One polite policy refusal with human escalation ticket (`create_ticket`) OR an unanswerable question handled gracefully ("I don't know / no information").
4. Real voice interaction using Gnani STT & TTS.

---

## ⏱️ Video Script Timeline (120 Seconds)

### [00:00 - 00:15] Introduction (15s)
- **Visual**: Show the terminal or IDE with the project folder.
- **You Say**: 
  > *"Hello everyone! This is our submission for VoiceOps 2026 for ZentroMart customer support. The agent uses Gnani STT for transcription, our Grounded Precedence-Aware RAG engine powered by Gemini, and Gnani TTS Kaveri for voice replies. Today's simulation date is 20 October 2026."*

---

### [00:15 - 00:45] Turn 1 & 2: Order Lookup & Identity Verification (30s)
- **Run command**: 
  ```bash
  python run.py --interactive
  ```
- **Customer**: *"Hello, mujhe order ke baare mein help chahiye."*
- **Agent Audio**: *"Hello! I am ZentroMart's AI support assistant. Could you please share your 8-digit order number so I can assist you?"*
- **Customer**: *"Order number hai 8978 2837."*
- **Agent Audio**: *"For security, could you please provide the last 4 digits of your registered phone number or your delivery pincode?"*
- **Customer**: *"Last four digits 4533 hain."*
- **Agent Audio**: *"Thank you Kabir, your identity has been verified. How can I help you with order 89782837 today?"*
- **Key point for judges**: Note that order details were protected behind the verification gate.

---

### [00:45 - 01:15] Turn 3: Grounded Answer & Contextual Follow-Up (30s)
- **Customer**: *"Kya main Kaafi Running Sneakers return kar sakti hoon?"*
- **Agent Audio**: Explains return window (15 calendar days from delivery date) grounded in `RET-2`.
- **Customer Follow-up**: *"Aur refund kitne din mein aayega?"*
- **Agent Audio**: Identifies payment mode is Wallet from order records, and explains wallet refund is instant within 2 hours (`REF-2`).
- **Key point for judges**: Notice conversational memory and coreference resolution without repeating order details.

---

### [01:15 - 01:45] Turn 4: Policy Refusal & Human Handover Ticket (30s)
- **Customer**: *"Mera 43-inch Smart TV damage ho gaya tha, aap abhi mere account mein ₹500 compensation transfer kar do."*
- **Agent Audio**: 
  > *"I have created a support ticket (TKT...) for this issue. A human specialist from our team will contact you shortly."*
- **Key point for judges**: The agent strictly refuses out-of-policy cash compensation and automatically creates a handover ticket because the claim is above ₹10,000.

---

### [01:45 - 02:00] Wrap-up & Batch Runner Command (15s)
- **Show Terminal**:
  ```bash
  python run.py --audio_dir sample_inputs/ --output_dir sample_outputs/
  ```
- **You Say**:
  > *"Our one-command batch runner processes folders of customer audio, logging transcripts, evidence section IDs, and generating spoken audio replies. Thank you!"*
