from pydantic import BaseModel, Field


class UrlCheckRequest(BaseModel):
    url: str = Field(min_length=5, max_length=800)
    page_text: str = ""


class UrlCheckResponse(BaseModel):
    normalized_url: str
    domain: str
    risk_score: int
    risk_level: str
    reasons: list[str]


class ScamReportCreate(BaseModel):
    url: str = Field(min_length=5, max_length=800)
    category: str = Field(min_length=2, max_length=60)
    comment: str = Field(default="", max_length=2000)
    reporter_hash: str = Field(default="anonymous", max_length=120)


class ScamReportResponse(BaseModel):
    id: int
    status: str
    created_at: str
