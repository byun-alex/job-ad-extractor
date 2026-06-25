"""Provider-agnostic LLM client.

Order of resolution:
1. ANTHROPIC_API_KEY  -> Anthropic Claude
2. OPENAI_API_KEY     -> OpenAI
3. neither            -> MockLLM (deterministic, offline) so the harness still
                         runs and the eval/validation pattern is demonstrable
                         without a key. Drop a key in .env to make it real.

The mock also supports a forced-malformed mode so we can prove the validation
layer actually rejects bad output (see scripts/demo_validation.py).
"""

from __future__ import annotations

import json
import os
import re


class LLMError(RuntimeError):
    pass


def _strip_fences(text: str) -> str:
    """Models love wrapping JSON in ```json fences. Strip them."""
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    return (fenced.group(1) if fenced else text).strip()


class AnthropicLLM:
    def __init__(self) -> None:
        import anthropic  # imported lazily so the dep is optional

        self.client = anthropic.Anthropic()
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
        self.name = f"anthropic:{self.model}"

    def complete(self, prompt: str) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return _strip_fences(msg.content[0].text)


class OpenAILLM:
    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.name = f"openai:{self.model}"

    def complete(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return _strip_fences(resp.choices[0].message.content or "")


class MockLLM:
    """Deterministic offline stand-in. Returns a plausible extraction by reading
    a few cues out of the prompt text. Not smart -- just enough to exercise the
    pipeline end to end with no API key."""

    name = "mock:offline"

    def __init__(self, mode: str = "valid") -> None:
        # mode: "valid" -> schema-conforming, "malformed" -> deliberately broken
        self.mode = mode

    def complete(self, prompt: str) -> str:
        if self.mode == "malformed":
            # salary_max < salary_min AND a bad enum -> must be rejected downstream
            return json.dumps(
                {
                    "title": "AI Automation Specialist",
                    "company": "Acme",
                    "location": "Sydney",
                    "employment_type": "freelance-ish",  # not in the enum
                    "salary_min": 90000,
                    "salary_max": 70000,  # max < min
                    "salary_currency": "AUD",
                    "seniority": "mid",
                    "remote": True,
                    "skills": ["Python", "Claude"],
                }
            )

        body = prompt.lower()
        return json.dumps(
            {
                "title": "AI Automation Specialist",
                "company": "Acme Pty Ltd",
                "location": "Sydney" if "sydney" in body else None,
                "employment_type": "full-time" if "full-time" in body else "unknown",
                "salary_min": 35 if "35" in body else None,
                "salary_max": 50 if "50" in body else None,
                "salary_currency": "AUD" if ("aud" in body or "$" in prompt) else None,
                "seniority": "junior" if "graduate" in body else "unknown",
                "remote": True if "remote" in body or "hybrid" in body else None,
                "skills": [s for s in ("Python", "Claude", "n8n", "Zapier")
                           if s.lower() in body],
            }
        )


def get_llm() -> AnthropicLLM | OpenAILLM | MockLLM:
    if os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicLLM()
    if os.getenv("OPENAI_API_KEY"):
        return OpenAILLM()
    return MockLLM()
