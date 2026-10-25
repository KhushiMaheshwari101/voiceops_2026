import argparse
import os
import sys
import json
import csv
from pathlib import Path

from src.config import SAMPLE_OUTPUTS_DIR
from src.agent import SupportAgent
from src.voice_agent import VoiceOpsAgent


def run_batch_audio(audio_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    voice_agent = VoiceOpsAgent()

    audio_extensions = {".wav", ".mp3", ".ogg", ".m4a"}
    audio_files = [p for p in audio_dir.iterdir() if p.suffix.lower() in audio_extensions]

    if not audio_files:
        print(f"No audio files found in {audio_dir}")
        return

    print(f"Processing {len(audio_files)} audio files from {audio_dir}...")
    results = []

    for idx, audio_path in enumerate(sorted(audio_files), start=1):
        print(f"\n[{idx}/{len(audio_files)}] Processing: {audio_path.name}")
        out_audio_name = f"reply_{audio_path.stem}.wav"
        out_audio_path = output_dir / out_audio_name

        turn_result = voice_agent.voice_turn(
            audio_path=str(audio_path),
            output_audio_path=str(out_audio_path),
        )

        record = {
            "input_file": audio_path.name,
            "transcript_heard": turn_result["transcript_heard"],
            "agent_reply": turn_result["agent_reply"],
            "reply_audio_file": out_audio_name if turn_result["audio_file"] else "N/A",
            "retrieved_chunks": " ; ".join(turn_result["retrieved_tokens"]),
        }
        results.append(record)

        # Save individual reply txt for automated evaluators
        reply_txt_path = output_dir / f"{audio_path.stem}_reply.txt"
        with open(reply_txt_path, "w", encoding="utf-8") as rf:
            rf.write(f"REPLY: {turn_result['agent_reply']}\nSOURCES: {' ; '.join(turn_result['retrieved_tokens'])}\n")

        print(f"  Heard: {record['transcript_heard']}")
        print(f"  Reply: {record['agent_reply']}")
        print(f"  Chunks: {record['retrieved_chunks']}")
        print(f"  Saved Audio: {record['reply_audio_file']}")

    # Save summary outputs
    json_path = output_dir / "batch_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    csv_path = output_dir / "batch_results.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"\nBatch completed! Results saved to:\n- {json_path}\n- {csv_path}")


def run_text_query(text: str):
    agent = SupportAgent(mode="step3")
    reply, chunks, tools = agent.respond(text)
    print("\n--- ZentroMart VoiceOps Support ---")
    print(f"Customer: {text}")
    print(f"Agent: {reply}")
    print(f"Retrieved Chunks: {chunks}")
    if tools:
        print(f"Tool Executed: {tools['tool']} -> {tools.get('result')}")


def run_interactive():
    print("\n=== ZentroMart VoiceOps Interactive Mode ===")
    print("Type your message (or 'exit' to quit):\n")
    agent = SupportAgent(mode="step3")

    while True:
        try:
            msg = input("Customer: ").strip()
            if not msg:
                continue
            if msg.lower() in ("exit", "quit"):
                break
            reply, chunks, tool_call = agent.respond(msg)
            print(f"Agent: {reply}")
            if chunks:
                print(f"[Evidence Chunks: {chunks}]")
            if tool_call:
                print(f"[Tool: {tool_call['tool']} -> {tool_call['result']}]")
            print()
        except KeyboardInterrupt:
            break


def main():
    parser = argparse.ArgumentParser(description="VoiceOps 2026 Batch Runner & CLI")
    # Positional args (optional)
    parser.add_argument("pos_audio_dir", nargs="?", type=str, help="Positional path to audio directory")
    parser.add_argument("pos_output_dir", nargs="?", type=str, help="Positional path to output directory")

    # Flag-based args
    parser.add_argument("--audio_dir", type=str, help="Path to folder containing customer audio files")
    parser.add_argument("--output_dir", type=str, default=str(SAMPLE_OUTPUTS_DIR), help="Output folder")
    parser.add_argument("--text", type=str, help="Run single text query")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive CLI chat")

    args = parser.parse_args()

    # Resolve audio directory from either flag or positional argument
    target_audio_dir = args.audio_dir or args.pos_audio_dir
    target_output_dir = args.pos_output_dir if args.pos_output_dir else args.output_dir

    if target_audio_dir:
        run_batch_audio(Path(target_audio_dir), Path(target_output_dir))
    elif args.text:
        run_text_query(args.text)
    elif args.interactive:
        run_interactive()
    else:
        # Default run demo question if no arguments passed
        print("No audio directory specified. Running demo query...")
        run_text_query("My order still hasn't arrived. Can I cancel it?")


if __name__ == "__main__":
    main()
