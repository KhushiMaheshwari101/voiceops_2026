import csv
import json
from pathlib import Path
from typing import Dict, Any, List

from src.config import PRACTICE_DIR, SAMPLE_OUTPUTS_DIR
from src.agent import SupportAgent


def check_includes(text: str, pattern: str) -> bool:
    """Checks if text contains required phrases (separated by ' ; ' for AND, ' / ' for OR)."""
    if not pattern:
        return True
    text_lower = text.lower()
    
    # Semicolon separates conditions that must all be satisfied
    and_conditions = [c.strip() for c in pattern.split(";") if c.strip()]
    for cond in and_conditions:
        # Slash separates alternatives (any one is sufficient)
        or_options = [opt.strip().lower() for opt in cond.split("/") if opt.strip()]
        matched_any = any(opt in text_lower for opt in or_options)
        if not matched_any:
            return False
    return True


def check_not_includes(text: str, pattern: str) -> bool:
    """Ensures none of the forbidden phrases appear."""
    if not pattern:
        return True
    text_lower = text.lower()
    for item in pattern.split(";"):
        phrase = item.strip().lower()
        if phrase and phrase in text_lower:
            return False
    return True


def check_evidence_match(retrieved: List[str], gold: str) -> float:
    """Calculates recall of gold evidence tokens in retrieved chunks."""
    if not gold:
        return 1.0
    gold_tokens = [t.strip() for t in gold.split(";") if t.strip()]
    if not gold_tokens:
        return 1.0

    matches = 0
    for gt in gold_tokens:
        if any(gt.lower() in r.lower() for r in retrieved):
            matches += 1
    return matches / len(gold_tokens)


def evaluate_questions(limit: int = 52, mode: str = "step2") -> Dict[str, Any]:
    questions_file = PRACTICE_DIR / "questions.csv"
    if not questions_file.exists():
        raise FileNotFoundError(f"Missing {questions_file}")

    with open(questions_file, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))[:limit]

    agent = SupportAgent(mode=mode)
    results = []

    correct_answers = 0
    total_retrieval_recall = 0.0
    unanswerable_handled = 0
    total_unanswerable = 0

    print(f"\n--- Running Evaluation: Mode={mode.upper()} on {len(rows)} Questions ---")

    for i, row in enumerate(rows, start=1):
        q_id = row.get("id", f"Q{i}")
        q_text = row.get("question", "")
        answerable = row.get("answerable", "True") == "True"
        must_inc = row.get("must_include", "")
        must_not = row.get("must_not_include", "")
        gold_ev = row.get("gold_evidence", "")

        reply, chunks, _ = agent.respond(q_text)

        inc_pass = check_includes(reply, must_inc)
        not_pass = check_not_includes(reply, must_not)
        answer_correct = inc_pass and not_pass

        recall = check_evidence_match(chunks, gold_ev) if mode == "step2" else 0.0

        if answer_correct:
            correct_answers += 1

        total_retrieval_recall += recall

        if not answerable:
            total_unanswerable += 1
            if answer_correct:
                unanswerable_handled += 1

        results.append({
            "id": q_id,
            "question": q_text,
            "reply": reply,
            "retrieved_chunks": chunks,
            "must_include": must_inc,
            "must_not_include": must_not,
            "is_correct": answer_correct,
            "evidence_recall": recall,
        })

        if i % 10 == 0 or i == len(rows):
            print(f"Evaluated {i}/{len(rows)} questions...")

    accuracy = (correct_answers / len(rows)) * 100
    avg_recall = (total_retrieval_recall / len(rows)) * 100
    unanswerable_rate = (unanswerable_handled / total_unanswerable * 100) if total_unanswerable else 100.0

    summary = {
        "mode": mode,
        "total_evaluated": len(rows),
        "correct_answers": correct_answers,
        "accuracy_pct": round(accuracy, 2),
        "evidence_recall_pct": round(avg_recall, 2),
        "unanswerable_handled_pct": round(unanswerable_rate, 2),
        "details": results,
    }

    out_file = SAMPLE_OUTPUTS_DIR / f"eval_results_{mode}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n[{mode.upper()} Summary]")
    print(f"Accuracy: {accuracy:.1f}% ({correct_answers}/{len(rows)})")
    if mode == "step2":
        print(f"Evidence Recall: {avg_recall:.1f}%")
        print(f"Hallucination Prevention (Unanswerable): {unanswerable_rate:.1f}%")

    return summary
