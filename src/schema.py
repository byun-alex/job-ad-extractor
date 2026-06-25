"""Structured-output schema for the extract_job task.

This is the contract every LLM output must satisfy. If the model returns
something that does not fit, validation fails LOUDLY here instead of letting
malformed data flow downstream.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class EmploymentType(str, Enum):
    full_time = "full-time"
    part_time = "part-time"
    casual = "casual"
    contract = "contract"
    internship = "internship"
    unknown = "unknown"


class Seniority(str, Enum):
    intern = "intern"
    junior = "junior"
    mid = "mid"
    senior = "senior"
    lead = "lead"
    unknown = "unknown"


class JobPosting(BaseModel):
    """One structured job posting extracted from a free-text ad."""

    # Reject unknown keys so a hallucinated extra field is a failure, not silent noise.
    model_config = {"extra": "forbid"}

    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    location: str | None = None
    employment_type: EmploymentType = EmploymentType.unknown
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    salary_currency: str | None = None
    seniority: Seniority = Seniority.unknown
    remote: bool | None = None
    skills: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _salary_band_is_ordered(self) -> "JobPosting":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError(
                f"salary_max ({self.salary_max}) is less than "
                f"salary_min ({self.salary_min})"
            )
        return self
