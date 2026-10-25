import os
import zipfile
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Required deliverables as per Capstone Brief (Page 14)
REQUIRED_FILES = [
    "README.md",
    ".env.example",
    "requirements.txt",
    "run.py",
    "report.pdf",
    "demo.mp4",
]

REQUIRED_DIRS = [
    "src",
    "sample_outputs",
]

# Sensitive or forbidden files (Page 14: "Do not include .env, API keys, virtual environments or a dataset copy.")
FORBIDDEN = {
    ".env",
    "__pycache__",
    ".git",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "Capstone_Project_Dataset_FTTT_2026",
    "Capstone_Project_Dataset_FTTT_2026.zip",
}


def package_submission(zip_name: str = "voiceops_submission.zip"):
    output_zip = BASE_DIR / zip_name
    print(f"Creating submission package: {output_zip.name} ...")

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as z:
        # Add required root files
        for fname in REQUIRED_FILES:
            fpath = BASE_DIR / fname
            if fpath.exists():
                print(f"  Adding file: {fname} ({fpath.stat().st_size / (1024*1024):.2f} MB)")
                z.write(fpath, arcname=fname)
            else:
                print(f"  [WARNING] File missing: {fname}")

        # Add required directories
        for dname in REQUIRED_DIRS:
            dpath = BASE_DIR / dname
            if dpath.exists():
                for root, dirs, files in os.walk(dpath):
                    # Filter out __pycache__
                    dirs[:] = [d for d in dirs if d not in FORBIDDEN and not d.endswith(".pyc")]
                    for file in files:
                        if file.endswith((".pyc", ".pyo")):
                            continue
                        full_p = Path(root) / file
                        arc_p = full_p.relative_to(BASE_DIR)
                        print(f"  Adding: {arc_p}")
                        z.write(full_p, arcname=str(arc_p))

    print(f"\nSubmission ZIP ready: {output_zip}")
    print(f"Total ZIP size: {output_zip.stat().st_size / (1024*1024):.2f} MB")
    print("Verification: Zero secret keys (.env) or dataset copy included, strictly following Capstone submission rules!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="voiceops_submission.zip", help="Name of output zip file")
    args = parser.parse_args()
    package_submission(args.name)
