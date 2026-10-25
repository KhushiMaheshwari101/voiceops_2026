import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Set page configuration
st.set_page_config(
    page_title="ZentroMart VoiceOps 2026",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load environment
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from src.agent import SupportAgent
from src.voice_agent import VoiceOpsAgent, normalize_text_for_speech
from src.config import REFERENCE_DATE

# Custom CSS for clean UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1rem;
        color: #4B5563;
        margin-bottom: 20px;
    }
    .chat-bubble-user {
        background-color: #E0E7FF;
        color: #1E1B4B;
        padding: 12px 16px;
        border-radius: 12px 12px 2px 12px;
        margin-bottom: 10px;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-bubble-agent {
        background-color: #F3F4F6;
        color: #111827;
        padding: 12px 16px;
        border-radius: 12px 12px 12px 2px;
        margin-bottom: 10px;
        border-left: 4px solid #2563EB;
        max-width: 80%;
    }
    .evidence-pill {
        display: inline-block;
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 5px;
        margin-top: 5px;
    }
    .ticket-badge {
        display: inline-block;
        background-color: #FEF3C7;
        color: #92400E;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
        border: 1px solid #F59E0B;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "agent" not in st.session_state:
    st.session_state.agent = SupportAgent(mode="step3")
if "voice_agent" not in st.session_state:
    st.session_state.voice_agent = VoiceOpsAgent(agent=st.session_state.agent)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="main-header">🎙️ ZentroMart VoiceOps 2026</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">IIT Guwahati &times; Gnani.ai Capstone | Simulation Date: <b>{REFERENCE_DATE}</b></div>', unsafe_allow_html=True)
with col2:
    if st.button("🔄 Reset Conversation"):
        st.session_state.agent.reset()
        st.session_state.messages = []
        st.rerun()

# Sidebar - Demo Presets & Controls
with st.sidebar:
    st.header("⚡ Quick Demo Presets")
    st.write("Click below to test key capstone scenarios instantly:")

    # Preset 1: High Value Damage Handover
    if st.button("📺 Demo 1: High Value Damage Handover"):
        st.session_state.agent.reset()
        st.session_state.messages = []
        preset_turns = [
            "Hello, mujhe order ke baare mein help chahiye.",
            "Order number hai 8978 2837.",
            "Last four digits 4533 hain.",
            "Maine Zentro Vista 43-inch 4K Smart TV damage report kiya tha. Abhi replacement approve kar do na?"
        ]
        for msg in preset_turns:
            reply, chunks, tool = st.session_state.agent.respond(msg)
            # Generate speech
            audio_path = BASE_DIR / f"sample_outputs/reply_demo_{len(st.session_state.messages)}.wav"
            st.session_state.voice_agent.synthesize_speech(reply, output_file=str(audio_path))
            st.session_state.messages.append({
                "user": msg,
                "agent": reply,
                "chunks": chunks,
                "tool": tool,
                "audio": str(audio_path) if audio_path.exists() else None
            })
        st.rerun()

    # Preset 2: Return & Wallet Refund Follow-up
    if st.button("👟 Demo 2: Return Window & Wallet Refund"):
        st.session_state.agent.reset()
        st.session_state.messages = []
        preset_turns = [
            "Hello, mujhe order ke baare mein help chahiye.",
            "Order number hai 1859 9253.",
            "Last four digits 4265 hain.",
            "Kya main Kaafi Running Sneakers return kar sakti hoon?",
            "Aur refund kitne din mein aayega?"
        ]
        for msg in preset_turns:
            reply, chunks, tool = st.session_state.agent.respond(msg)
            audio_path = BASE_DIR / f"sample_outputs/reply_demo_{len(st.session_state.messages)}.wav"
            st.session_state.voice_agent.synthesize_speech(reply, output_file=str(audio_path))
            st.session_state.messages.append({
                "user": msg,
                "agent": reply,
                "chunks": chunks,
                "tool": tool,
                "audio": str(audio_path) if audio_path.exists() else None
            })
        st.rerun()

    # Preset 3: Unanswerable Hallucination Refusal
    if st.button("🚫 Demo 3: Strict Policy / Refusal"):
        st.session_state.agent.reset()
        st.session_state.messages = []
        msg = "Can I schedule a delivery at midnight?"
        reply, chunks, tool = st.session_state.agent.respond(msg)
        audio_path = BASE_DIR / "sample_outputs/reply_demo_unanswerable.wav"
        st.session_state.voice_agent.synthesize_speech(reply, output_file=str(audio_path))
        st.session_state.messages.append({
            "user": msg,
            "agent": reply,
            "chunks": chunks,
            "tool": tool,
            "audio": str(audio_path) if audio_path.exists() else None
        })
        st.rerun()

    st.divider()
    st.markdown("### 🛠️ Architecture Settings")
    st.info("**Voice Engine**: Gnani STT (REST) + TTS\n\n**Voice Model**: `timbre-v2.5` (Kaveri)\n\n**LLM**: Gemini 2.5 Flash\n\n**Precedence**: Policy > Guide > Help > FAQ")

# Main Chat Display
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.info("💡 Start a conversation by typing below, uploading an audio clip, or clicking one of the Demo Presets on the left!")
    else:
        for idx, m in enumerate(st.session_state.messages):
            # User Message
            st.markdown(f'<div class="chat-bubble-user">👤 <b>Customer:</b> {m["user"]}</div>', unsafe_allow_html=True)
            
            # Agent Message
            st.markdown(f'<div class="chat-bubble-agent">🤖 <b>ZentroMart AI:</b> {m["agent"]}</div>', unsafe_allow_html=True)
            
            # Evidence & Tool details
            meta_cols = st.columns([2, 1])
            with meta_cols[0]:
                if m.get("chunks"):
                    pills = "".join([f'<span class="evidence-pill">📄 {c}</span>' for c in m["chunks"]])
                    st.markdown(f"<b>Retrieved Evidence:</b> {pills}", unsafe_allow_html=True)
                if m.get("tool"):
                    t_info = m["tool"]
                    if t_info.get("tool") == "create_ticket" and t_info.get("result", {}).get("created"):
                        tid = t_info["result"].get("ticket_id")
                        st.markdown(f'<span class="ticket-badge">🎫 Ticket Created: {tid}</span>', unsafe_allow_html=True)
                    elif t_info.get("tool") == "lookup_order":
                        res = t_info.get("result", {})
                        status = "✅ Verified" if res.get("verified") else "🔒 Verification Required"
                        st.caption(f"🔧 Tool: `lookup_order` ({status})")
            
            with meta_cols[1]:
                if m.get("audio") and os.path.exists(m["audio"]):
                    st.audio(m["audio"], format="audio/wav")

# Audio Upload & Text Input
st.divider()
input_col1, input_col2 = st.columns([1, 2])

with input_col1:
    uploaded_audio = st.file_uploader("🎙️ Upload Customer Audio (.wav)", type=["wav", "mp3", "m4a"], key="audio_uploader")
    if uploaded_audio is not None:
        if st.button("Transcribe & Process Audio"):
            temp_path = BASE_DIR / "sample_inputs/uploaded_temp.wav"
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(uploaded_audio.getbuffer())
            
            with st.spinner("Gnani STT transcribing & processing..."):
                result = st.session_state.voice_agent.voice_turn(
                    audio_path=str(temp_path),
                    output_audio_path=str(BASE_DIR / f"sample_outputs/reply_upload_{len(st.session_state.messages)}.wav")
                )
                st.session_state.messages.append({
                    "user": result["transcript_heard"],
                    "agent": result["agent_reply"],
                    "chunks": result["retrieved_tokens"],
                    "tool": result["tool_calls"],
                    "audio": result["audio_file"]
                })
                st.rerun()

with input_col2:
    user_text = st.chat_input("Type customer message here...")
    if user_text:
        with st.spinner("Processing..."):
            reply, chunks, tool = st.session_state.agent.respond(user_text)
            audio_path = BASE_DIR / f"sample_outputs/reply_chat_{len(st.session_state.messages)}.wav"
            st.session_state.voice_agent.synthesize_speech(reply, output_file=str(audio_path))
            st.session_state.messages.append({
                "user": user_text,
                "agent": reply,
                "chunks": chunks,
                "tool": tool,
                "audio": str(audio_path) if audio_path.exists() else None
            })
            st.rerun()
