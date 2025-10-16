from pydantic import BaseModel, Field, field_validator
from typing import List, Literal

Verdict = Literal["strong match", "possible match", "not a match"]

class CVScore(BaseModel):
    match_score: int = Field(ge=0, le=100, description="0–100")
    summary: str
    strengths: List[str]
    missing_requirements: List[str]
    verdict: Verdict

    @field_validator("summary")
    @classmethod
    def clean_summary(cls, v: str) -> str:
        return v.strip()
