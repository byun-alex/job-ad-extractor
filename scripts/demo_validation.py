"""Proof that the validation layer rejects malformed model output.

Runs the same extract step twice against the offline mock:
  1. a well-formed output  -> accepted, returns a JobPosting
  2. a deliberately broken output (bad enum + salary_max < salary_min)
       -> rejected, logged, NOT passed downstream

Run:  python -m scripts.demo_validation
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.extract import extract_job  # noqa: E402
from src.llm import MockLLM  # noqa: E402

SAMPLE = (
    "AI Automation Specialist, Sydney, hybrid, full-time, $35-50/hr. "
    "Python, Claude, n8n, Zapier. Graduate welcome."
)


def main() -> int:
    print("=== Case 1: well-formed output ===")
    good = extract_job(SAMPLE, version="v2", llm=MockLLM(mode="valid"))
    assert good.ok, "expected valid output to be accepted"
    print("ACCEPTED:", good.posting.title, "@", good.posting.company)

    print("\n=== Case 2: malformed output (bad enum + salary_max < salary_min) ===")
    bad = extract_job(SAMPLE, version="v2", llm=MockLLM(mode="malformed"))
    assert not bad.ok, "expected malformed output to be REJECTED"
    assert bad.posting is None, "rejected output must not pass downstream"
    print("REJECTED as expected:", bad.error)

    print("\nValidation layer works: bad output stopped at the gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
