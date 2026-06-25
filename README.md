# job-ad-extractor

Turns a messy, free-text **job ad into clean structured JSON** — with
**prompt versioning**, **structured-output validation**, and an **eval harness**:
the reliability layer that turns "an LLM call I wrote" into "an LLM call I can
prove behaves."

Task: messy free-text **job ad → strict JSON** (`JobPosting`).

## Why this exists

LLM steps fail quietly: a model returns prose instead of JSON, drops a field,
invents an enum value, or gives a salary band where max < min — and the bad
data flows downstream. This project stops that at a validation gate, versions
the prompts so output changes are traceable, and **measures** extraction quality
against a golden set so "it works" is a number, not a vibe.

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
- **Eval runner + golden set** (`src/evaluate.py`, `data/golden.json`) — scores
  the extractor against 8 hand-labelled cases field-by-field (exact match for
  scalars/enums, Jaccard overlap for the skills list), and emits a headline
  pass rate + field accuracy.
- **Regression check** — each run is compared to the previous one; a case that
  passed before and fails now is flagged. Tie it to a prompt version and a
  regression reads as "v2 dropped case 7 vs v1".
- **Markdown report** — `reports/eval_report.md`, a per-case table + headline
  metric (generated; gitignored).

## Run it

```bash
pip install -r requirements.txt

# prove the validation gate (offline, no key needed):
python -m scripts.demo_validation

# run one extraction on a sample ad:
python -m src.extract

# score the extractor against the golden set (writes reports/eval_report.md):
python -m src.evaluate            # prompt v2
python -m src.evaluate --version v1   # compare an older prompt
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

The eval report looks like this (per-case, with the headline metric up top):

```
- Headline: 7/8 cases pass (88%), field accuracy 94%
- vs last run: up +13 pts (was 75% on anthropic:claude-haiku-4-5/v2)

| Case                  | Result  | Failing fields                  |
|-----------------------|---------|---------------------------------|
| c1-atlassian-senior   | ✅ pass | —                               |
| c2-graduate-analyst   | ✅ pass | —                               |
| c5-lead-ml-remote     | ❌ fail | salary_currency (want USD, ...) |
```

> Numbers above are illustrative of a real model run. With the **offline mock**
> (no key) the runner still works end to end but scores a low baseline — the
> mock returns the same canned answer for every ad, which the eval correctly
> flags. The real headline metric comes from running with an API key.

## Use a real model

Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`).
No code change — `get_llm()` picks it up automatically, for both extraction and
evaluation.

## Layout

```
prompts/        versioned prompt files + CHANGELOG       (M1)
src/schema.py   pydantic contract for the output         (M2)
src/llm.py      provider-agnostic client + offline mock
src/extract.py  prompt -> LLM -> JSON -> validated JobPosting (M2)
src/evaluate.py golden-set scorer + regression + report  (M3-M6)
data/golden.json hand-labelled eval cases                (M3)
scripts/        demo_validation.py
logs/, reports/ generated output (gitignored)
```

## Roadmap

- [x] **M1** prompt versioning
- [x] **M2** structured-output validation
- [x] **M3** golden dataset
- [x] **M4** eval runner (exact-match + skills overlap)
- [x] **M5** regression check vs last run
- [x] **M6** Markdown report with headline metric
- [ ] LLM-as-judge for fuzzy fields · live deploy · demo GIF
