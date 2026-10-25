# VoiceOps 2026 — ZentroMart AI Customer Support Voice Agent

> **Capstone Project**: LLM & Generative AI Course · Consulting & Analytics Club, IIT Guwahati × Gnani.ai  
> **Author**: Khushi Maheshwari  
> **Simulation Reference Date**: 20 October 2026  
> **Public Repository**: [https://github.com/KhushiMaheshwari101/voiceops_2026](https://github.com/KhushiMaheshwari101/voiceops_2026)  

---

## 📖 Overview

**VoiceOps 2026** is a production-grade, grounded conversational AI support agent built for **ZentroMart**, an Indian online grocery and electronics store. It accepts customer audio calls, transcribes speech using **Gnani STT**, reasons over enterprise policies and synthetic databases using a **Precedence-Aware RAG Engine** and **Gemini LLM**, performs identity verification and order actions via mock tools, and replies back with natural spoken audio using **Gnani TTS (`timbre-v2.5`)**.

```
[ Customer Audio ]
       │
       ▼
 [ Gnani STT ] ──────────────► (en-IN transcript)
                                      │
                                      ▼
                      [ ZentroMart Support Brain ]
                      ├── Precedence RAG (21 KB Docs)
                      ├── Caller Identity Verification (lookup_order)
                      ├── Calendar & Business Day Engine (20 Oct 2026)
                      └── Escalation / Handover (create_ticket)
                                      │
                                      ▼
 [ Gnani TTS ] ◄────────────── (Spoken Text Reply)
       │
       ▼
[ Spoken Voice Reply (.wav) ]
```

---

## 🛠️ Key Capabilities & Compliance

1. **Grounded Answers & Hallucination Prevention**:
   - Indexes 21 Knowledge Base markdown documents (`kb/*.md`) with preserved section IDs (`[RET-1]`, `[REF-2]`, etc.).
   - Follows strict precedence: `Current Policy` $\rightarrow$ `Agent Guide` $\rightarrow$ `Help` $\rightarrow$ `FAQ` $\rightarrow$ `Marketing`.
   - Never hallucinates: if an inquiry is not supported by documentation (e.g. midnight delivery, student discounts), the agent politely states that information is unavailable and offers a human connection.
2. **Identity Verification Gate**:
   - Order details are protected behind identity verification. The caller must provide the **last 4 digits of their registered phone number** OR the **6-digit delivery pincode**.
   - The agent strictly enforces a maximum of 1 retry and never leaks customer data.
3. **Calendar & Business Day Engine**:
   - Frozen reference date: **20 October 2026**.
   - Business days: Monday through Saturday, skipping official warehouse holidays (`holidays.csv`). Return windows use calendar days.
4. **Speech-Ready Text Normalization**:
   - Order IDs are spoken in spaced digit groups (`8 9 7 8 2 8 3 7`).
   - Dates are formatted for clear pronunciation (`the 24th of October 2026`).
   - Amounts are voiced in words (`forty-nine rupees`).
5. **Human Handover & Escalation**:
   - Generates human handover tickets (`create_ticket`) for high-value damages (> ₹10,000), repeat contacts, safety concerns, or direct human agent requests.

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+
- Valid `GNANI_API_KEY` (from [app.gnani.ai/voice](https://app.gnani.ai/voice))
- Valid `GEMINI_API_KEY` (from [aistudio.google.com](https://aistudio.google.com))

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
In `.env`:
```env
GNANI_API_KEY=your_gnani_key_here
GEMINI_API_KEY=your_gemini_key_here
```

---

## 💻 Running the Agent

### Official Batch Run Command (Evaluator Ready)
Takes a folder of customer audio files, transcribes each with Gnani STT, processes it through the grounded agent, synthesizes voice replies with Gnani TTS, and outputs transcripts, replies, and retrieved sources:
```bash
# Standard command
python run.py --audio_dir /path/to/customer_audio_folder --output_dir sample_outputs/

# Or positional syntax
python run.py /path/to/customer_audio_folder sample_outputs/

# Or via Shell script
./run.sh /path/to/customer_audio_folder sample_outputs/
```

### Interactive Web UI (Streamlit)
Launch the visual web application with 1-click demo presets, audio playback, and evidence badges:
```bash
streamlit run app.py
```

### Automated Terminal Walkthrough Demo
Experience the full conversation with audio spoken through your laptop speakers:
```bash
python demo.py
```

### Quick Text Query Mode
Test specific questions directly in the terminal:
```bash
python run.py --text "My order still hasn't arrived. Can I cancel it?"
```

---

## 📊 Submission Deliverables

```
team_name_voiceops.zip
├── README.md                    # Setup and exact run commands
├── .env.example                 # Example environment variables (no secrets)
├── requirements.txt             # Required Python libraries
├── run.py / run.sh              # Batch evaluation command
├── report.pdf                   # Official 3-page Capstone Technical Report
├── demo.mp4                     # 2-minute demo video
├── src/                         # Modular codebase
│   ├── config.py                # Environment & dynamic dataset resolver
│   ├── calendar_util.py         # Business days (Mon-Sat, holidays) & return windows
│   ├── kb_indexer.py            # Chunker and precedence metadata extractor
│   ├── retriever.py             # Hybrid lexical & dense search with precedence ranking
│   ├── tools_adapter.py         # Verification and ticket creation wrapper
│   ├── llm_client.py            # Gemini API client with retry and fallback
│   ├── agent.py                 # Multi-turn conversational state machine
│   ├── voice_agent.py           # Gnani STT & TTS integration + speech normalizer
│   └── evaluator.py             # Automated Step 1 vs Step 2 benchmark evaluator
└── sample_outputs/              # Batch run outputs, transcripts, audio replies
```
