"""The extract_job step: prompt -> LLM -> JSON -> validated JobPosting.

This is where Milestone 2 lives: every model output is parsed and validated
against the schema. Malformed output (bad JSON, missing field, broken enum,
salary_max < salary_min) is caught and LOGGED, never passed downstream.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .llm import MockLLM, get_llm
from .schema import JobPosting

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "extract.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("extract_job")


def load_prompt(version: str = "v2") -> str:
    path = PROMPTS_DIR / f"extract_job.{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"No prompt at {path}")
    return path.read_text(encoding="utf-8")


@dataclass
class ExtractResult:
    ok: bool
    prompt_version: str
    model: str
    posting: JobPosting | None = None
    error: str | None = None
    raw: str | None = None


def extract_job(job_text: str, version: str = "v2", llm=None) -> ExtractResult:
    """Run one extraction. Never raises on bad model output -- returns ok=False
    with the reason logged, so a caller (the eval runner) can score it."""
    llm = llm or get_llm()
    prompt = load_prompt(version).replace("{job_text}", job_text)

    raw = llm.complete(prompt)

    # Guard 1: parseable JSON?
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        msg = f"output is not valid JSON: {e}"
        log.error("[%s|%s] REJECTED %s", llm.name, version, msg)
        return ExtractResult(False, version, llm.name, error=msg, raw=raw)

    # Guard 2: conforms to the schema?
    try:
        posting = JobPosting.model_validate(data)
    except ValidationError as e:
        first = e.errors()[0]
        msg = f"schema validation failed at {first['loc']}: {first['msg']}"
        log.error("[%s|%s] REJECTED %s", llm.name, version, msg)
        return ExtractResult(False, version, llm.name, error=msg, raw=raw)

    log.info("[%s|%s] OK -> %s @ %s", llm.name, version, posting.title, posting.company)
    return ExtractResult(True, version, llm.name, posting=posting, raw=raw)


if __name__ == "__main__":
    sample = (
        "We're hiring an AI Automation Specialist in Sydney (hybrid). Full-time, "
        "$35-50/hr. You'll build automations with Python, Claude, n8n and Zapier. "
        "Recent graduate welcome."
    )
    result = extract_job(sample, version="v2")
    if result.ok:
        print(result.posting.model_dump_json(indent=2))
    else:
        print("REJECTED:", result.error)
