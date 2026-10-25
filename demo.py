import time
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.agent import SupportAgent
from src.voice_agent import VoiceOpsAgent
from src.config import REFERENCE_DATE

# Try importing winsound for Windows audio playback
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


def play_audio(file_path: str):
    if HAS_WINSOUND and os.path.exists(file_path):
        try:
            winsound.PlaySound(file_path, winsound.SND_FILENAME)
        except Exception:
            pass


def print_banner():
    print("\n" + "=" * 65)
    print("      🎙️  ZENTROMART VOICEOPS 2026 — OFFICIAL DEMO WALKTHROUGH")
    print(f"      IIT Guwahati x Gnani.ai Capstone | Simulation Date: {REFERENCE_DATE}")
    print("=" * 65 + "\n")


def run_demo():
    print_banner()
    agent = SupportAgent(mode="step3")
    voice_agent = VoiceOpsAgent(agent=agent)

    scenarios = [
        {
            "title": "SCENARIO 1: Order Lookup & Identity Verification Gate",
            "turns": [
                ("Customer", "Hello, mujhe order ke baare mein help chahiye."),
                ("Customer", "Order number hai 8978 2837."),
                ("Customer", "Last four digits 4533 hain."),
            ]
        },
        {
            "title": "SCENARIO 2: High-Value Damage & Policy Refusal with Human Escalation",
            "turns": [
                ("Customer", "Maine Zentro Vista 43-inch 4K Smart TV damage report kiya tha. Abhi replacement approve kar do na?"),
            ]
        },
        {
            "title": "SCENARIO 3: Strict Hallucination Prevention (Unanswerable Question)",
            "turns": [
                ("Customer", "Can I schedule a delivery at midnight?"),
            ]
        }
    ]

    turn_counter = 1
    out_dir = BASE_DIR / "sample_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    for sc in scenarios:
        print(f"\n>>> {sc['title']} <<<\n")
        time.sleep(1)

        for speaker, msg in sc["turns"]:
            print(f"[{turn_counter}] {speaker}: {msg}")
            
            # Agent processing
            reply, chunks, tools = agent.respond(msg)
            
            # Synthesize real voice
            audio_out = out_dir / f"demo_turn_{turn_counter}.wav"
            voice_agent.synthesize_speech(reply, output_file=str(audio_out))
            
            print(f"    🤖 ZentroMart AI: {reply}")
            if chunks:
                print(f"    📄 Evidence Chunks: {chunks}")
            if tools:
                if tools["tool"] == "create_ticket" and tools["result"].get("created"):
                    print(f"    🎫 Human Handover Ticket Created: {tools['result'].get('ticket_id')}")
                elif tools["tool"] == "lookup_order":
                    v_status = "Verified" if tools["result"].get("verified") else "Verification Required"
                    print(f"    🔧 Tool Call: lookup_order (Status: {v_status})")
            
            # Speak audio through laptop speakers
            if audio_out.exists():
                print(f"    🔊 [Playing audio voice reply...]")
                play_audio(str(audio_out))

            print("-" * 65)
            turn_counter += 1
            time.sleep(1.5)

    print("\n✅ Walkthrough complete! All audio replies saved to sample_outputs/")
    print("=" * 65)


if __name__ == "__main__":
    run_demo()
