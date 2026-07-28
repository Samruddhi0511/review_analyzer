"""
main.py — FastAPI backend for the Customer Feedback Analyzer.

Routes:
    POST /reviews          — Submit a review; LLM analyses it; result saved to DB.
    GET  /reviews          — Retrieve all reviews.
    GET  /admin/summary    — LLM-generated insights + aggregate stats.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db, insert_review, get_all_reviews, get_stats
from backend.llm import analyze_review, generate_summary
from backend.models import ReviewRequest

app = FastAPI(
    title="Customer Feedback Analyzer API",
    description="Sentiment analysis for restaurant reviews powered by Groq LLM.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    """Initialise the SQLite database on server start."""
    init_db()


# ── Health check ──────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Customer Feedback Analyzer API is running."}


# ── User routes ───────────────────────────────────────────────────

@app.post("/reviews", tags=["Reviews"])
def submit_review(request: ReviewRequest):
    """
    Accept a raw review, call the LLM to get sentiment + score,
    persist to SQLite, and return the full result.
    """
    text = request.review_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Review text cannot be empty.")

    try:
        analysis = analyze_review(text)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    review_id = insert_review(
        review_text=text,
        sentiment=analysis["sentiment"],
        score=analysis["score"],
    )

    return {
        "id": review_id,
        "review_text": text,
        "sentiment": analysis["sentiment"],
        "score": analysis["score"],
        "reason": analysis.get("reason", ""),
    }


@app.get("/reviews", tags=["Reviews"])
def list_reviews():
    """Return all reviews from the database, newest first."""
    return get_all_reviews()


# ── Admin routes ──────────────────────────────────────────────────

@app.get("/admin/summary", tags=["Admin"])
def admin_summary():
    """
    Return aggregate stats + LLM-generated one-line summaries of what
    positive and negative reviews are mainly about.
    """
    reviews = get_all_reviews()
    stats   = get_stats()

    try:
        llm_summary = generate_summary(reviews)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "total":            stats["total"] or 0,
        "positive_count":   stats["positive_count"] or 0,
        "negative_count":   stats["negative_count"] or 0,
        "avg_score":        stats["avg_score"] or 0.0,
        "positive_summary": llm_summary["positive_summary"],
        "negative_summary": llm_summary["negative_summary"],
    }
