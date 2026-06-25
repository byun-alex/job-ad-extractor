# extract_job — v2

You extract structured data from a messy, free-text job advertisement.

Return ONLY a single JSON object — no prose, no markdown code fences, no trailing commentary.

Schema (every key required; use null / "unknown" when the ad does not state a value):
- title: string — the role title, trimmed
- company: string — hiring company; "Unknown" if absent
- location: string or null — city/region, or null if remote-only or unstated
- employment_type: one of ["full-time", "part-time", "casual", "contract", "internship", "unknown"]
- salary_min: number or null — lower bound as a plain number, no currency symbols or commas
- salary_max: number or null — upper bound; must be >= salary_min when both are present
- salary_currency: string or null — ISO-style code, e.g. "AUD", "USD"
- seniority: one of ["intern", "junior", "mid", "senior", "lead", "unknown"]
- remote: boolean or null — true if remote/hybrid is offered, false if explicitly on-site, null if unstated
- skills: array of strings — concrete tools, languages, or platforms named (deduplicated)

Rules:
- Infer seniority from cues ("intern"/"graduate" -> intern/junior; "lead"/"head of" -> lead).
- Normalise salaries to numbers: "$35-50/hr" -> salary_min 35, salary_max 50, currency "AUD" only if AUD is implied.
- Never invent skills that are not in the text.

Job ad:
"""
{job_text}
"""
