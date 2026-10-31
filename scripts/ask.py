"""Ask questions from the terminal (tests the full pipeline without Streamlit).

Usage:
    python scripts/ask.py "What are the responsibilities of an internal auditor?"
    python scripts/ask.py --mode retrieval "What is the risk appetite?"
    python scripts/ask.py            # interactive loop
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.chatbot.assistant import MODE_RAG, MODE_RETRIEVAL, APDISAssistant  # noqa: E40


def show(assistant: APDISAssistant, question: str, mode: str, top_k: int) -> None:
    result = assistant.ask(question, mode=mode, top_k=top_k)
    print("\n" + "=" * 70)
    print(result.answer)
    print("\nSources:")
    for ref in result.references:
        print(f"  • {ref}")
    if result.model:
        print(f"\n(model: {result.model})")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="*")
    parser.add_argument("--mode", choices=[MODE_RAG, MODE_RETRIEVAL], default=MODE_RAG)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    assistant = APDISAssistant()
    if not assistant.documents():
        print("The vector database is empty. Run: python scripts/ingest.py")
        return

    if args.question:
        show(assistant, " ".join(args.question), args.mode, args.top_k)
        return

    print("APDIS interactive mode. Type a question, or 'exit' to quit.")
    while True:
        try:
            q = input("\nQuestion> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"exit", "quit", "q"}:
            break
        if q:
            try:
                show(assistant, q, args.mode, args.top_k)
            except Exception as exc:  # noqa: BLE001
                print(f"Error: {exc}")


if __name__ == "__main__":
    main()
