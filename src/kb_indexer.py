import os
import re
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import KB_DIR, DATA_DIR


DOC_TYPE_PRECEDENCE = {
    "policy": 1,
    "agent_guide": 2,
    "help": 3,
    "faq": 4,
    "marketing": 5,
    "meta": 6,
}


class KBChunk:
    def __init__(
        self,
        section_id: str,
        section_title: str,
        content: str,
        doc_id: str,
        doc_title: str,
        doc_type: str,
        status: str,
        effective_from: str,
        version: str,
        filename: str,
    ):
        self.section_id = section_id
        self.section_title = section_title
        self.content = content
        self.doc_id = doc_id
        self.doc_title = doc_title
        self.doc_type = doc_type
        self.status = status
        self.effective_from = effective_from
        self.version = version
        self.filename = filename

        # Compute precedence score (lower is higher priority)
        base_rank = DOC_TYPE_PRECEDENCE.get(doc_type.lower(), 10)
        if status.lower() == "superseded":
            self.precedence = 99
        else:
            self.precedence = base_rank

    @property
    def full_text(self) -> str:
        return f"[{self.section_id}] {self.section_title}\n{self.content}".strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "section_title": self.section_title,
            "content": self.content,
            "doc_id": self.doc_id,
            "doc_title": self.doc_title,
            "doc_type": self.doc_type,
            "status": self.status,
            "effective_from": self.effective_from,
            "version": self.version,
            "filename": self.filename,
            "precedence": self.precedence,
        }


def parse_frontmatter(text: str) -> tuple[Dict[str, str], str]:
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body


def load_kb_chunks() -> List[KBChunk]:
    chunks = []
    if not KB_DIR.exists():
        return chunks

    for filepath in sorted(KB_DIR.glob("*.md")):
        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()

        meta, body = parse_frontmatter(raw_text)
        doc_id = meta.get("doc_id", filepath.stem)
        doc_title = meta.get("title", filepath.stem)
        doc_type = meta.get("doc_type", "general")
        status = meta.get("status", "current")
        effective_from = meta.get("effective_from", "")
        version = meta.get("version", "1.0")

        # Split sections using markdown headers with section tags: ## [ID] Title
        # or fallback to ## Title
        section_pattern = re.compile(r"^##\s+(?:\[([A-Z0-9_\-\.]+)\]\s*)?(.*?)$", re.MULTILINE)
        matches = list(section_pattern.finditer(body))

        if not matches:
            # Whole file is single chunk
            chunks.append(
                KBChunk(
                    section_id=doc_id,
                    section_title=doc_title,
                    content=body.strip(),
                    doc_id=doc_id,
                    doc_title=doc_title,
                    doc_type=doc_type,
                    status=status,
                    effective_from=effective_from,
                    version=version,
                    filename=filepath.name,
                )
            )
        else:
            for i, match in enumerate(matches):
                sec_id = match.group(1) or f"{doc_id}_{i+1}"
                sec_title = match.group(2).strip()
                start_pos = match.end()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(body)
                sec_content = body[start_pos:end_pos].strip()

                chunks.append(
                    KBChunk(
                        section_id=sec_id,
                        section_title=sec_title,
                        content=sec_content,
                        doc_id=doc_id,
                        doc_title=doc_title,
                        doc_type=doc_type,
                        status=status,
                        effective_from=effective_from,
                        version=version,
                        filename=filepath.name,
                    )
                )

    return chunks


def load_products_catalog() -> Dict[str, Dict[str, Any]]:
    products_file = DATA_DIR / "products.csv"
    catalog = {}
    if products_file.exists():
        with open(products_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku = row.get("sku", "").strip()
                if sku:
                    catalog[sku] = row
    return catalog


def load_pincodes_catalog() -> Dict[str, Dict[str, Any]]:
    pincodes_file = DATA_DIR / "pincodes.csv"
    pins = {}
    if pincodes_file.exists():
        with open(pincodes_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pincode = row.get("pincode", "").strip()
                if pincode:
                    pins[pincode] = row
    return pins
