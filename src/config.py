import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")


def resolve_dataset_dir() -> Path:
    """Dynamically resolve dataset directory for automated testing harnesses."""
    # 1. Custom ENV var
    env_dir = os.getenv("DATASET_DIR")
    if env_dir and Path(env_dir).exists():
        return Path(env_dir)

    # 2. Local Capstone_Project_Dataset_FTTT_2026 directory
    sub_dir = BASE_DIR / "Capstone_Project_Dataset_FTTT_2026"
    if sub_dir.exists() and (sub_dir / "kb").exists():
        return sub_dir

    # 3. Direct in BASE_DIR (if extracted into root)
    if (BASE_DIR / "kb").exists() and (BASE_DIR / "data").exists():
        return BASE_DIR

    # 4. In parent directory
    parent_sub = BASE_DIR.parent / "Capstone_Project_Dataset_FTTT_2026"
    if parent_sub.exists() and (parent_sub / "kb").exists():
        return parent_sub
    if (BASE_DIR.parent / "kb").exists() and (BASE_DIR.parent / "data").exists():
        return BASE_DIR.parent

    # Default fallback
    return sub_dir


DATASET_DIR = resolve_dataset_dir()
DATA_DIR = DATASET_DIR / "data"
KB_DIR = DATASET_DIR / "kb"
PRACTICE_DIR = DATASET_DIR / "practice"
TOOLS_DIR = DATASET_DIR / "tools"
SAMPLE_OUTPUTS_DIR = BASE_DIR / "sample_outputs"

GNANI_API_KEY = os.getenv("GNANI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Fixed simulation date
REFERENCE_DATE = "2026-10-20"

# Gnani Voice Settings
GNANI_TTS_MODEL = "timbre-v2.5"
GNANI_TTS_VOICE = "Kaveri"
GNANI_LANGUAGE_CODE = "en-IN"

# Ensure output directory exists
SAMPLE_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
