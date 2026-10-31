"""Evaluate retrieval (and optionally Gemini answers) on evaluation/test_questions.json.

Metrics
  Retrieval
    Hit@1 / Hit@k  - the expected (source, page) is the top result / within top-k
    MRR            - mean reciprocal rank of the expected page
  Gemini RAG (--rag)
    Keyword recall - share of expected key facts present in the answer
    Abstention     - for unanswerable questions, did the model say it doesn't know?
    Citations      - answer contains [n] citations

Usage:
    python scripts/evaluate.py              # retrieval only, no API calls
    python scripts/evaluate.py --rag        # also call Gemini (one request per question)
    python scripts/evaluate.py --questions evaluation/test_questions_real.json
"""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.chatbot.assistant import MODE_RAG, APDISAssistant
from src.utils import config

EVAL_FILE = config.PROJECT_ROOT / "evaluation" / "test_questions.json"
OUT_FILE = config.PROJECT_ROOT / "evaluation" / "results.csv"
ABSTAIN_MARKERS = ["do not contain", "does not contain", "not contain enough", "no information", "not mentioned", "not available", "not provided"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rag", action="store_true", help="also evaluate Gemini answers")
    parser.add_argument("--top-k", type=int, default=config.TOP_K)
    parser.add_argument("--delay", type=float, default=7.0, help="seconds between Gemini calls (free-tier rate limit)")
    parser.add_argument("--questions", default=str(EVAL_FILE), help="question file (e.g. evaluation/test_questions_real.json)")
    args = parser.parse_args()

    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    assistant = APDISAssistant()
    indexed = set(assistant.documents())
    rows, hits1, hitsk, rr, n_ret = [], 0, 0, 0.0, 0
    kw_scores, abstain_ok, n_unans, cited = [], 0, 0, 0

    for q in questions:
        unanswerable = q.get("unanswerable", False)
        if not unanswerable and q["source"] not in indexed:
            print(f"  skip #{q['id']}: {q['source']} not ingested")
            continue

        results = assistant.retriever.retrieve(q["question"], top_k=args.top_k)
        ranked = [(r.source, r.page) for r in results]
        row = {"id": q["id"], "question": q["question"], "top_result": f"{ranked[0][0]} p{ranked[0][1]}" if ranked else "", "top_score": results[0].score if results else ""}

        if not unanswerable:
            n_ret += 1
            # "pages" lists every acceptable page (a fact may appear on several);
            # older files use a single "page".
            pages = q.get("pages") or [q["page"]]
            targets = {(q["source"], p) for p in pages}
            rank = next((i for i, hit in enumerate(ranked, 1) if hit in targets), None)
            hits1 += rank == 1
            hitsk += rank is not None
            rr += 1 / rank if rank else 0
            row["expected"] = f"{q['source']} p{'/'.join(map(str, pages))}"
            row["rank"] = rank or "miss"

        if args.rag:
            try:
                answer = assistant.ask(q["question"], mode=MODE_RAG, top_k=args.top_k).answer
            except Exception as exc:  # noqa: BLE001
                answer = f"ERROR: {exc}"
            row["answer"] = answer.replace("\n", " ")
            low = answer.lower()
            if unanswerable:
                n_unans += 1
                ok = any(m in low for m in ABSTAIN_MARKERS)
                abstain_ok += ok
                row["abstained"] = ok
            else:
                kws = q.get("keywords", [])
                score = sum(k.lower() in low for k in kws) / len(kws) if kws else 1.0
                kw_scores.append(score)
                row["keyword_recall"] = round(score, 2)
                cited += bool(re.search(r"\[\d+(?:\s*,\s*\d+)*\]", answer))
            time.sleep(args.delay)

        rows.append(row)
        print(f"  #{q['id']:>2} rank={row.get('rank', '-'):<4} {q['question'][:70]}")

    print("\n" + "=" * 60)
    if n_ret:
        print(f"Retrieval  (n={n_ret}, k={args.top_k})")
        print(f"  Hit@1 : {hits1 / n_ret:.0%}")
        print(f"  Hit@{args.top_k} : {hitsk / n_ret:.0%}")
        print(f"  MRR   : {rr / n_ret:.3f}")
    if args.rag and kw_scores:
        print("Gemini RAG")
        print(f"  Keyword recall      : {sum(kw_scores) / len(kw_scores):.0%}")
        print(f"  Answers with citations: {cited}/{len(kw_scores)}")
        if n_unans:
            print(f"  Correct abstentions : {abstain_ok}/{n_unans}")

    fields = sorted({k for r in rows for k in r}, key=lambda k: ["id", "question", "expected", "rank", "top_result", "top_score", "answer", "keyword_recall", "abstained"].index(k))
    with OUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nDetailed results: {OUT_FILE.relative_to(config.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
