"""Optional credential-dependent read-only probe. Never prints keys, URLs or documents."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pydantic import BaseModel
from intelligence.provider.llm import provider, ProviderUnavailable, speech_provider


class Probe(BaseModel):
    ok: bool


async def main():
    if not provider.configured:
        print("LLM: skipped; credentials/model/provider are not configured.")
    else:
        try:
            result = Probe.model_validate(
                await provider.structured(
                    'Return {"ok":true}.', Probe.model_json_schema()
                )
            )
            print("LLM: connected" if result.ok else "LLM: unavailable")
        except (ProviderUnavailable, ValueError):
            print("LLM: unavailable; deterministic fallback remains ready.")
    print(
        "Speech: configured; validate an actual Malayalam audio file from the operator UI."
        if speech_provider.configured
        else "Speech: skipped; no configured provider. Explicit demo transcript remains ready."
    )


if __name__ == "__main__":
    asyncio.run(main())
