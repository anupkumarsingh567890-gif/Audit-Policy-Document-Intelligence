"""Measure where the time goes for one question.

Usage:  python scripts/benchmark.py
        python scripts/benchmark.py "your question"

Prints timings for: loading the embedding model, retrieval, and Gemini
(time to first word and total) for each model x thinking setting.
Uses about 6 Gemini requests.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from src.utils import config

QUESTION = " ".join(sys.argv[1:]) or "Within how many days must an NBFC report fraud to RBI?"


def main() -> None:
    print(f"Question: {QUESTION}\n")

    t = time.perf_counter()
    from src.chatbot.assistant import APDISAssistant
    from src.llm.gemini import GeminiClient, GeminiError

    assistant = APDISAssistant()
    print(f"Load embedding model + database : {time.perf_counter() - t:6.2f} s  (once per app start)")

    assistant.retrieve(QUESTION)  # warm-up
    t = time.perf_counter()
    results, _ = assistant.retrieve(QUESTION)
    print(f"Retrieval (embed + search)      : {time.perf_counter() - t:6.2f} s")
    prompt = build_user_prompt(QUESTION, results)
    print(f"Prompt size                     : {len(prompt):,} characters\n")

    models = [config.GEMINI_MODEL] + [m for m in config.GEMINI_FALLBACK_MODELS if m != config.GEMINI_MODEL]
    print(f"{'model':<28}{'thinking':<10}{'first word':>12}{'total':>9}  result")
    print("-" * 80)
    for model in models:
        for thinking in ("off", "low"):
            client = GeminiClient(model=model, fallback_models=[], thinking=thinking)
            t = time.perf_counter()
            first = None
            try:
                text = ""
                for piece in client.generate_stream(SYSTEM_PROMPT, prompt):
                    if first is None:
                        first = time.perf_counter() - t
                    text += piece
                total = time.perf_counter() - t
                status = "ok: " + text.strip().replace("\n", " ")[:28]
                print(f"{model:<28}{thinking:<10}{first:>10.2f} s{total:>7.2f} s  {status}")
            except GeminiError as exc:
                total = time.perf_counter() - t
                reason = "rate-limited" if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc) else str(exc)[:40]
                print(f"{model:<28}{thinking:<10}{'-':>12}{total:>7.2f} s  FAILED ({reason})")
            time.sleep(4)  # stay under the free-tier per-minute limit

    print("\nSend this output to Claude.")


if __name__ == "__main__":
    main()
