"""
agent.py — Auto-Response Agent for negative reviews.


How it works:
1. When a review comes in negative, we call the LLM again with a set
   of "tools" (functions) it can choose to call.
2. The LLM decides which tool(s) to call based on the review content —
   we are not hardcoding if/else logic, the model reasons about it.
3. We execute whatever tool the model picked and store the result.

This is a routing agent pattern: classify -> decide -> act.
"""

import json
from groq import Groq
from backend.database import get_connection  

client = Groq()  

MODEL = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# STEP 1: Define the tools (functions) the agent is allowed to call.
# Each one maps to a real Python function below.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "flag_for_manager_review",
            "description": (
                "Flag a review for a human manager to look at. Use this "
                "for anything serious: health/safety complaints, rude "
                "staff, or repeated issues. Do NOT use for minor gripes "
                "like 'a bit slow service'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "review_id": {"type": "integer"},
                    "urgency": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "How urgently a human should look at this",
                    },
                    "reason": {
                        "type": "string",
                        "description": "One sentence on why this needs human attention",
                    },
                },
                "required": ["review_id", "urgency", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_response",
            "description": (
                "Draft a short, polite customer-facing reply to a "
                "negative review, acknowledging the issue. You MUST start "
                "the draft with 'Thank you for your feedback.'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "review_id": {"type": "integer"},
                    "tone": {
                        "type": "string",
                        "enum": ["apologetic", "reassuring", "corrective"],
                    },
                    "draft_text": {"type": "string"},
                },
                "required": ["review_id", "tone", "draft_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_repeat_complaint",
            "description": (
                "Search past reviews in the database for a keyword to see "
                "if this is part of a recurring pattern (e.g. 'cold food' "
                "mentioned 3+ times this week)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The core complaint keyword to search for, e.g. 'cold food'",
                    }
                },
                "required": ["keyword"],
            },
        },
    },
]


# ---------------------------------------------------------------------------

def flag_for_manager_review(review_id: int, urgency: str, reason: str) -> str:
    conn = get_connection()
    conn.execute(
        "UPDATE reviews SET flagged = 1, urgency = ?, flag_reason = ? WHERE id = ?",
        (urgency, reason, review_id),
    )
    conn.commit()
    return f"Flagged review {review_id} as {urgency} priority: {reason}"


def draft_response(review_id: int, tone: str, draft_text: str) -> str:
    conn = get_connection()
    conn.execute(
        "UPDATE reviews SET draft_response = ?, response_tone = ? WHERE id = ?",
        (draft_text, tone, review_id),
    )
    conn.commit()
    return f"Drafted a {tone} response for review {review_id}"


def check_repeat_complaint(keyword: str) -> str:
    conn = get_connection()
    cur = conn.execute(
        "SELECT COUNT(*) FROM reviews WHERE review_text LIKE ? AND created_at >= datetime('now', '-7 days')",
        (f"%{keyword}%",),
    )
    count = cur.fetchone()[0]
    if count >= 3:
        return f"TREND DETECTED: '{keyword}' mentioned {count} times in the last 7 days."
    return f"'{keyword}' mentioned {count} times in the last 7 days — not yet a trend."


# Map tool name -> actual function, so we can call whichever one the model picks
AVAILABLE_FUNCTIONS = {
    "flag_for_manager_review": flag_for_manager_review,
    "draft_response": draft_response,
    "check_repeat_complaint": check_repeat_complaint,
}


# ---------------------------------------------------------------------------
# STEP 3: The agent loop itself.
# Call this after your existing sentiment analysis, only when sentiment == negative.
# ---------------------------------------------------------------------------

def run_negative_review_agent(review_id: int, review_text: str) -> dict:
    """
    Given a negative review, let the LLM decide which tool(s) to call,
    execute them, and return a log of what the agent did.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that handles negative restaurant "
                "reviews. Decide which of the available tools to use, "
                "if any. You can call more than one tool if needed "
                "(e.g. flag AND draft a response). Be judicious — not "
                "every negative review needs manager escalation."
            ),
        },
        {
            "role": "user",
            "content": f"Review ID: {review_id}\nReview text: {review_text}",
        },
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    message = response.choices[0].message
    actions_taken = []

    if message.tool_calls:
        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            func = AVAILABLE_FUNCTIONS.get(func_name)
            if func:
                result = func(**func_args)
                actions_taken.append({"tool": func_name, "args": func_args, "result": result})
    else:
        actions_taken.append({"tool": None, "result": "Agent decided no action was needed."})

    return {"review_id": review_id, "actions": actions_taken}