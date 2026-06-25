# Prompt changelog — extract_job

Prompts are versioned so an eval run can be tied to an exact prompt version.
A regression then reads as "v2 scored lower than v1 on case 7", not a mystery.

## extract_job

### v2 — 2026-06-26
- Made every schema key required (was implicitly optional in v1).
- Added explicit enum lists for `employment_type` and `seniority`.
- Added normalisation rules: salary parsing (`$35-50/hr` -> min/max), seniority
  inference from cues, dedup skills, `remote` tri-state.
- Added the `salary_max >= salary_min` constraint, restated in the schema.
- Hardened the "JSON only, no fences" instruction.

### v1 — 2026-06-26
- Initial prompt. Extracts title/company/location/employment_type/salary/
  seniority/remote/skills from a free-text job ad as JSON.
