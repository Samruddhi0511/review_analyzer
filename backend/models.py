from pydantic import BaseModel, Field


# ── Incoming request from Streamlit ──────────────────────────────
class ReviewRequest(BaseModel):
    review_text: str = Field(..., min_length=1, description="The raw customer review text")


# ── What the LLM returns after analysing a single review ─────────
class AnalysisResult(BaseModel):
    sentiment: str          # "positive" | "negative"
    score: int              # 1-5
    reason: str             # one-line explanation


# ── Full review row returned to the client ───────────────────────
class ReviewResponse(BaseModel):
    id: int
    review_text: str
    sentiment: str
    score: int
    reason: str
    created_at: str


# ── Admin summary endpoint response ─────────────────────────────
class AdminSummary(BaseModel):
    total: int
    positive_count: int
    negative_count: int
    avg_score: float
    positive_summary: str
    negative_summary: str
