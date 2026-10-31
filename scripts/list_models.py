"""List the Gemini models your API key can use, and run a tiny test call.

Usage:  python scripts/list_models.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.llm.gemini import GeminiClient, GeminiError  # noqa: E402
from src.utils import config  # noqa: E402


def main() -> None:
    try:
        client = GeminiClient()
    except GeminiError as exc:
        print(exc)
        return

    print("Models available to your key that can generate text:\n")
    for name in client.list_models():
        marker = "  <- configured" if name == config.GEMINI_MODEL else ""
        print(f"  {name}{marker}")

    print(f"\nTest call with '{config.GEMINI_MODEL}' (fallbacks: {', '.join(config.GEMINI_FALLBACK_MODELS)})…")
    try:
        reply = client.generate("Reply in one short sentence.", "Say hello to the APDIS project.")
        print(f"  ✓ {client.last_model_used}: {reply}")
    except GeminiError as exc:
        print(f"  ✗ {exc}")


if __name__ == "__main__":
    main()
