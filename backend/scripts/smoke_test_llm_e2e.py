"""End-to-end: LLMClient -> FallbackChain -> real provider."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

from app.services.ai.llm_client import get_llm_client  # noqa: E402


async def main() -> None:
    client = get_llm_client()
    print("chain:", client._chain.name)

    # Test generate_completion
    out = await client.generate_completion(
        system_prompt="You are terse.",
        user_prompt="Reply with exactly one word: OK",
        temperature=0.0,
        max_tokens=8,
    )
    print("generate_completion:", repr(out.strip()))

    # Test generate_json
    out_json = await client.generate_json(
        system_prompt="You produce JSON.",
        user_prompt='Return {"status":"ok","n":42}',
        temperature=0.0,
    )
    print("generate_json:", out_json)

    # Test chat_completion (the path chat_engine uses)
    out_chat = await client.chat_completion(
        messages=[
            {"role": "system", "content": "You are terse."},
            {"role": "user", "content": "Say HELLO"},
        ],
        temperature=0.0,
        max_tokens=8,
    )
    print("chat_completion:", repr(out_chat.strip()))


asyncio.run(main())
