# extract_job — v1

You extract structured data from a messy, free-text job advertisement.

Return ONLY a JSON object. No prose, no markdown fences, no explanation.

Schema:
- title: string — the role title
- company: string — hiring company; use "Unknown" if absent
- location: string or null
- employment_type: one of "full-time", "part-time", "casual", "contract", "internship", "unknown"
- salary_min: number or null — lower bound, plain number (no symbols)
- salary_max: number or null — upper bound
- salary_currency: string or null — e.g. "AUD", "USD"
- seniority: one of "intern", "junior", "mid", "senior", "lead", "unknown"
- remote: boolean or null
- skills: array of strings — concrete tools/skills named in the ad

If a field is not stated, use null (or "unknown"/"Unknown" where the schema is a string enum).

Job ad:
"""
{job_text}
"""
