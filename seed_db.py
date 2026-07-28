"""
seed_db.py — Loads sample_reviews.txt into the database via the FastAPI backend.

Usage (with FastAPI already running):
    python seed_db.py

Each review is POSTed to POST /reviews, which triggers LLM analysis and DB insertion.
This will make ~20 Groq API calls — should complete in ~30–60 seconds.
"""
import re
import sys
import time
from pathlib import Path

import requests

API_BASE = "http://localhost:8000"
REVIEWS_FILE = Path(__file__).parent / "sample_reviews.txt"


def parse_reviews(path: Path) -> list[str]:
    """Strip leading number + period from lines like '1. The food was...'"""
    reviews = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        # Remove leading "N. " prefix
        cleaned = re.sub(r"^\d+\.\s*", "", line)
        if cleaned:
            reviews.append(cleaned)
    return reviews


def seed():
    reviews = parse_reviews(REVIEWS_FILE)
    if not reviews:
        print("No reviews found in sample_reviews.txt")
        sys.exit(1)

    print(f"Found {len(reviews)} reviews to seed.\n")

    # Check backend is up
    try:
        requests.get(f"{API_BASE}/", timeout=5)
    except requests.exceptions.ConnectionError:
        print("❌  Cannot reach the FastAPI backend.")
        print("    Start it first:  uvicorn backend.main:app --reload")
        sys.exit(1)

    success, failed = 0, 0
    for i, review in enumerate(reviews, start=1):
        try:
            resp = requests.post(
                f"{API_BASE}/reviews",
                json={"review_text": review},
                timeout=40,
            )
            if resp.status_code == 200:
                data = resp.json()
                sentiment = data["sentiment"].upper()
                score = data["score"]
                print(f"[{i:02d}/{len(reviews)}] ✅  {sentiment}  ⭐{score}  — {review[:60]}...")

                # Negative reviews trigger the agent — show what it decided
                agent_actions = data.get("agent_actions", [])
                for action in agent_actions:
                    tool = action.get("tool")
                    if tool:
                        print(f"           🤖  agent → {tool}: {action['result']}")
                    else:
                        print(f"           🤖  agent → {action['result']}")

                success += 1
            else:
                print(f"[{i:02d}/{len(reviews)}] ❌  HTTP {resp.status_code}: {resp.text[:80]}")
                failed += 1
        except Exception as e:
            print(f"[{i:02d}/{len(reviews)}] ❌  Error: {e}")
            failed += 1

        
        time.sleep(0.5)

    print(f"\nDone! {success} seeded successfully, {failed} failed.")


if __name__ == "__main__":
    seed()