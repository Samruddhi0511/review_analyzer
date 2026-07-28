"""
llm.py — Groq API integration for review analysis and admin summary generation.
Uses llama-3.3-70b-versatile with JSON mode for reliable structured output.
"""
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client: Groq | None = None
MODEL = "llama-3.3-70b-versatile"


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file (get a free key at https://console.groq.com)."
            )
        _client = Groq(api_key=api_key)
    return _client


# ── Single-review analysis ────────────────────────────────────────

def analyze_review(review_text: str) -> dict:
    """
    Send a review to the LLM and get back:
        { "sentiment": "positive"|"negative", "score": 1-5, "reason": "..." }
    """
    prompt = f"""You are a restaurant review sentiment analyzer.

Analyze the following restaurant review and respond with a JSON object containing exactly these three keys:
- "sentiment": either "positive" or "negative" (choose based on the overall tone)
- "score": an integer from 1 to 5, where 1 = very bad and 5 = very good
- "reason": one short sentence (max 15 words) explaining the score

Review:
\"\"\"{review_text}\"\"\"

Respond ONLY with valid JSON. No extra text, no markdown."""

    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        result = json.loads(raw)
        # Sanitise / enforce types
        result["sentiment"] = str(result.get("sentiment", "negative")).lower().strip()
        if result["sentiment"] not in ("positive", "negative"):
            result["sentiment"] = "negative"
        result["score"] = max(1, min(5, int(result.get("score", 3))))
        result["reason"] = str(result.get("reason", ""))
        return result
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        raise RuntimeError(f"LLM returned unexpected output: {raw}") from exc


# ── Admin summary ─────────────────────────────────────────────────

def generate_summary(reviews: list[dict]) -> dict:
    """
    Given all reviews, ask the LLM to produce one-line summaries for what
    positive and negative reviews are mainly about.

    Returns:
        { "positive_summary": "...", "negative_summary": "..." }
    """
    if not reviews:
        return {
            "positive_summary": "No reviews submitted yet.",
            "negative_summary": "No reviews submitted yet.",
        }

    positives = [r["review_text"] for r in reviews if r["sentiment"] == "positive"]
    negatives  = [r["review_text"] for r in reviews if r["sentiment"] == "negative"]

    positive_block = "\n".join(f"- {t}" for t in positives) if positives else "None"
    negative_block = "\n".join(f"- {t}" for t in negatives) if negatives else "None"

    prompt = f"""You are a restaurant business analyst. Below are customer reviews grouped by sentiment.

POSITIVE REVIEWS:
{positive_block}

NEGATIVE REVIEWS:
{negative_block}

Based on these reviews, respond with a JSON object with exactly two keys:
- "positive_summary": One sentence (max 25 words) starting with "Positive reviews mainly highlight..." that describes the main themes praised by customers.
- "negative_summary": One sentence (max 25 words) starting with "Negative reviews mainly highlight..." that describes the main complaints or issues raised.

If there are no positive reviews, set "positive_summary" to "No positive reviews have been submitted yet."
If there are no negative reviews, set "negative_summary" to "No negative reviews have been submitted yet."

Respond ONLY with valid JSON. No extra text."""

    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        result = json.loads(raw)
        return {
            "positive_summary": str(result.get("positive_summary", "N/A")),
            "negative_summary": str(result.get("negative_summary", "N/A")),
        }
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"LLM returned unexpected output: {raw}") from exc
