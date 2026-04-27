"""Hit each configured LLM provider with a tiny prompt to verify keys work."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

from app.config import settings  # noqa: E402
from app.services.ai.llm_provider import _build_provider  # noqa: E402


async def main() -> None:
    for name in ("groq", "cerebras", "gemini"):
        print(f"\n--- {name} ---")
        p = _build_provider(name, settings)
        if p is None:
            print("  not configured, skipped")
            continue
        try:
            out = await p.complete(
                system_prompt="You are terse.",
                user_prompt="Reply with exactly: PONG",
                temperature=0.0,
                max_tokens=8,
            )
            print(f"  OK: {out.strip()!r}")
        except Exception as e:
            print(f"  FAIL: {type(e).__name__}: {e}")
        finally:
            aclose = getattr(p, "aclose", None)
            if aclose:
                await aclose()


asyncio.run(main())
