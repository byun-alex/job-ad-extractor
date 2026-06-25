# llm-eval-harness

A small, production-shaped harness for **structured LLM extraction** with
**prompt versioning** and **schema validation** — the reliability layer that
turns "an LLM call I wrote" into "an LLM call I can prove behaves."

Task: messy free-text **job ad → strict JSON** (`JobPosting`).

> Roadmap: this repo is being built in milestones. **Shipped so far:**
> prompt versioning (M1) and structured-output validation (M2). Eval runner +
> golden set + regression check + report are next (M3–M6).

## Why this exists

LLM steps fail quietly: a model returns prose instead of JSON, drops a field,
invents an enum value, or gives a salary band where max < min — and the bad
data flows downstream. This harness stops that at a gate, and versions the
prompts so output changes are traceable to a prompt change.

## What works today

- **Versioned prompts** — `prompts/extract_job.v1.md`, `…v2.md`, with a
  `CHANGELOG.md`. An output can be tied to an exact prompt version, so a
  regression reads as "v2 vs v1 on case 7", not a mystery.
- **Structured-output validation** — every model output is parsed as JSON and
  validated against a pydantic schema (`src/schema.py`). Malformed output is
  **rejected and logged**, never passed downstream:
  - not valid JSON → rejected
  - missing/extra field (`extra="forbid"`) → rejected
  - bad enum (`employment_type`, `seniority`) → rejected
  - `salary_max < salary_min` → rejected (custom validator)
- **Provider-agnostic client** (`src/llm.py`) — uses Anthropic or OpenAI if a
  key is present, else a deterministic **offline mock** so the harness runs
  with zero setup.

## Run it

```bash
pip install -r requirements.txt

# prove the validation gate (offline, no key needed):
python -m scripts.demo_validation

# run one extraction on a sample ad:
python -m src.extract
```

Sample output:

```json
{
  "title": "AI Automation Specialist",
  "company": "Acme Pty Ltd",
  "location": "Sydney",
  "employment_type": "full-time",
  "salary_min": 35.0,
  "salary_max": 50.0,
  "salary_currency": "AUD",
  "seniority": "junior",
  "remote": true,
  "skills": ["Python", "Claude", "n8n", "Zapier"]
}
```

`demo_validation` shows a well-formed output accepted and a deliberately broken
one rejected at the gate.

## Use a real model

Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`).
No code change — `get_llm()` picks it up automatically.

## Layout

```
prompts/      versioned prompt files + CHANGELOG   (M1)
src/schema.py pydantic contract for the output     (M2)
src/llm.py    provider-agnostic client + mock
src/extract.py prompt -> LLM -> JSON -> validated JobPosting (M2)
scripts/      demo_validation.py
logs/         extract.log  (gitignored)
```

## Next (M3–M6)

Golden dataset (8–15 cases) · eval runner with exact-match + LLM-as-judge ·
regression check vs last run · Markdown report with a headline metric.
