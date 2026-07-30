from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=5, max_length=300, examples=["Impact of AI on jobs"])
    max_subquestions: int = Field(3, ge=1, le=5)


class ResearchResponse(BaseModel):
    topic: str
    report: str
    sources: list[str]
    report_location: str | None = None
    request_id: str
