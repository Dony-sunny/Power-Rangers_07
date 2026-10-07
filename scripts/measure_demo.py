"""Backwards-compatible measured evidence command."""

from generate_measured_results import generate
import json
from pathlib import Path

if __name__ == "__main__":
    result = generate()
    (
        Path(__file__).resolve().parent.parent / "data/demo/measured-results.json"
    ).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["judge_metrics"], indent=2))
