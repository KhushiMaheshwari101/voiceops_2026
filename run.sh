#!/bin/bash
# VoiceOps 2026 Batch Runner Shell Script
AUDIO_DIR=${1:-"sample_inputs"}
OUTPUT_DIR=${2:-"sample_outputs"}

python3 run.py --audio_dir "$AUDIO_DIR" --output_dir "$OUTPUT_DIR"
