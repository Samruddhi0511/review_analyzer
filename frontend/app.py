"""
app.py — Streamlit frontend for the Customer Feedback Analyzer.

Two roles:
  • Customer  — submit a review; see instant AI sentiment + score.
  • Admin     — password-protected dashboard with LLM insights & full review table.
"""
import streamlit as st
import requests
import pandas as pd

API_BASE = "http://localhost:8000"
ADMIN_PASSWORD = "admin123"

# ── Page config (must be first Streamlit call) ────────────────────
st.set_page_config(
    page_title="Restaurant Feedback Analyzer",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base reset */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

.stApp {
    background: linear-gradient(135deg, #0d0d1a 0%, #1a1a2e 55%, #16213e 100%) !important;
    min-height: 100vh;
}

.main .block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1100px !important;
}

/* ── Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }

/* ── Hero title */
.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #f5a623 0%, #ff6b6b 50%, #c471ed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    line-height: 1.15;
    margin-bottom: 0.4rem;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.5);
    text-align: center;
    margin-bottom: 2.5rem;
    font-weight: 400;
}

/* ── Role selection cards */
.role-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 2.2rem 1.5rem;
    text-align: center;
    transition: all 0.25s ease;
}

/* ── Section header */
.section-header {
    font-size: 1.15rem;
    font-weight: 700;
    color: rgba(255,255,255,0.9);
    margin: 1.8rem 0 0.8rem 0;
    letter-spacing: 0.01em;
}

/* ── Insight cards */
.insight-positive {
    background: rgba(0, 212, 170, 0.07);
    border: 1px solid rgba(0, 212, 170, 0.25);
    border-left: 4px solid #00d4aa;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}

.insight-negative {
    background: rgba(255, 107, 107, 0.07);
    border: 1px solid rgba(255, 107, 107, 0.25);
    border-left: 4px solid #ff6b6b;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}

.insight-label-pos {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #00d4aa;
    margin-bottom: 0.45rem;
}

.insight-label-neg {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #ff6b6b;
    margin-bottom: 0.45rem;
}

.insight-text {
    font-size: 0.97rem;
    color: rgba(255,255,255,0.82);
    line-height: 1.55;
}

/* ── Result card after review submission */
.result-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    padding: 2rem 1.5rem;
    margin-top: 1.5rem;
    text-align: center;
}

/* ── Divider */
.thin-divider {
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 1.8rem 0;
}

/* ── Metric cards */
div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 16px !important;
    padding: 1rem !important;
}

/* Force ALL text inside metric to white */
div[data-testid="metric-container"] * {
    color: #ffffff !important;
}

/* Label — pure white */
div[data-testid="metric-container"] label,
div[data-testid="metric-container"] [data-testid="stMetricLabel"],
div[data-testid="metric-container"] [data-testid="stMetricLabel"] * {
    color: #ffffff !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

/* Value number — pure white, bold */
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] *,
div[data-testid="metric-container"] [data-testid="stMetricValue"],
div[data-testid="metric-container"] [data-testid="stMetricValue"] * {
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 2rem !important;
}

/* ── Primary buttons */
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #f5a623 0%, #e8473f 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    box-shadow: 0 4px 18px rgba(245, 166, 35, 0.25) !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 7px 24px rgba(245, 166, 35, 0.38) !important;
}

/* ── Text area */
div[data-testid="stTextArea"] textarea {
    background: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 12px !important;
    color: #111111 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}

div[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(245, 166, 35, 0.8) !important;
    box-shadow: 0 0 0 2px rgba(245, 166, 35, 0.25) !important;
}

/* ── Password input */
div[data-testid="stTextInput"] input {
    background: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 10px !important;
    color: #111111 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Dataframe */
div[data-testid="stDataFrame"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

/* ── Spinner */
div[data-testid="stSpinner"] {
    color: #f5a623 !important;
}

/* ── Alert/info/warning/success */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
}

/* ── Label text colour */
div[data-testid="stTextArea"] label,
div[data-testid="stTextInput"] label {
    color: rgba(255,255,255,0.6) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session state initialisation ──────────────────────────────────
def _init_state():
    defaults = {
        "role": None,           # None | "user" | "admin_login" | "admin"
        "admin_authed": False,
        "last_result": None,    # result dict from last review submission
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()


# ── Helpers ───────────────────────────────────────────────────────
def _stars(score: int) -> str:
    return "⭐" * score + "☆" * (5 - score)


def _go(role: str):
    st.session_state.role = role
    st.rerun()


# ═════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ═════════════════════════════════════════════════════════════════
def show_landing():
    st.markdown('<p class="hero-title">Restaurant Feedback Analyzer</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-subtitle">AI-powered sentiment analysis — understand every dining experience instantly</p>',
        unsafe_allow_html=True,
    )

    # Spacer
    st.write("")

    # Two role cards + buttons
    _, c1, gap, c2, _ = st.columns([1, 3, 0.5, 3, 1])

    with c1:
        st.markdown("""
        <div class="role-card">
            <div style="font-size:1.2rem;font-weight:700;color:white;margin-bottom:0.3rem;">Customer</div>
            <div style="font-size:0.85rem;color:rgba(255,255,255,0.45);">Share your dining experience and get instant AI feedback</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("I'm a Customer", use_container_width=True, key="btn_user"):
            _go("user")

    with c2:
        st.markdown("""
        <div class="role-card">
            <div style="font-size:1.2rem;font-weight:700;color:white;margin-bottom:0.3rem;">Admin</div>
            <div style="font-size:0.85rem;color:rgba(255,255,255,0.45);">View analytics, AI insights, and the full review database</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Admin Login", use_container_width=True, key="btn_admin"):
            _go("admin_login")


# ═════════════════════════════════════════════════════════════════
#  ADMIN LOGIN
# ═════════════════════════════════════════════════════════════════
def show_admin_login():
    st.markdown('<p class="hero-title" style="font-size:2.4rem">Admin Login</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Enter your password to access the analytics dashboard</p>', unsafe_allow_html=True)

    _, col, _ = st.columns([1.5, 2, 1.5])
    with col:
        st.write("")
        pwd = st.text_input("Password", type="password", placeholder="Enter admin password", key="admin_pwd_input")

        st.write("")
        if st.button("Login", use_container_width=True, key="btn_login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authed = True
                _go("admin")
            else:
                st.error("❌ Incorrect password. Try again.")

        st.write("")
        if st.button("← Back to Home", use_container_width=False, key="btn_back_login"):
            _go(None)


# ═════════════════════════════════════════════════════════════════
#  CUSTOMER VIEW
# ═════════════════════════════════════════════════════════════════
def show_user_view():
    # Top nav
    if st.button("← Home", key="btn_user_back"):
        st.session_state.last_result = None
        _go(None)

    st.markdown('<p class="hero-title" style="font-size:2.4rem;margin-top:0.5rem">Share Your Experience</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Tell us about your visit — our AI will analyse your feedback in seconds</p>', unsafe_allow_html=True)

    _, col, _ = st.columns([0.5, 4, 0.5])
    with col:
        review_text = st.text_area(
            "Your Review",
            placeholder="e.g. The pasta was incredible and the staff were super friendly. Would love to come back!",
            height=160,
            key="review_input",
            label_visibility="collapsed",
        )

        st.write("")
        submit = st.button("Analyse My Review", use_container_width=True, key="btn_submit_review")

        if submit:
            if not review_text.strip():
                st.warning("⚠️ Please write a review before submitting.")
            else:
                with st.spinner("Analysing your feedback with AI..."):
                    try:
                        resp = requests.post(
                            f"{API_BASE}/reviews",
                            json={"review_text": review_text.strip()},
                            timeout=40,
                        )
                        if resp.status_code == 200:
                            st.session_state.last_result = resp.json()
                        else:
                            detail = resp.json().get("detail", resp.text)
                            st.error(f"❌ Server error: {detail}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ **Cannot connect to the backend.** Make sure FastAPI is running:\n```\nuvicorn backend.main:app --reload\n```")
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {e}")

        # ── Result card
        result = st.session_state.last_result
        if result:
            sentiment = result["sentiment"]
            score     = result["score"]
            reason    = result.get("reason", "")
            agent_actions = result.get("agent_actions", [])

            is_positive = (sentiment == "positive")
            badge_color  = "#00d4aa" if is_positive else "#ff6b6b"
            badge_bg     = "rgba(0,212,170,0.15)" if is_positive else "rgba(255,107,107,0.15)"
            badge_border = "rgba(0,212,170,0.35)" if is_positive else "rgba(255,107,107,0.35)"

            draft_text = ""
            for action in agent_actions:
                if action.get("tool") == "draft_response":
                    draft_text = action.get("args", {}).get("draft_text", "")
                    break

            draft_html = ""
            if draft_text:
                draft_html = f'''
<div style="margin-top:1.5rem;text-align:left;background:rgba(255,255,255,0.03);padding:1.2rem;border-radius:12px;border:1px solid rgba(255,255,255,0.1);">
    <div style="font-size:0.75rem;font-weight:700;color:rgba(255,255,255,0.5);text-transform:uppercase;margin-bottom:0.5rem;letter-spacing:0.05em;">AI Drafted Response</div>
    <div style="font-size:0.95rem;color:rgba(255,255,255,0.9);line-height:1.5;font-style:italic;">"{draft_text}"</div>
</div>
'''

            st.markdown(f"""
            <div class="result-card">
                <div style="font-size:1.6rem;font-weight:700;color:white;margin-bottom:0.7rem">
                    Thank you for your feedback!
                </div>
                <div style="margin-bottom:1rem">
                    <span style="
                        background:{badge_bg};
                        color:{badge_color};
                        border:1px solid {badge_border};
                        padding:0.25rem 0.9rem;
                        border-radius:999px;
                        font-size:0.82rem;
                        font-weight:700;
                        letter-spacing:0.05em;
                        text-transform:uppercase;
                    ">{sentiment}</span>
                </div>
                <div style="font-size:1.9rem;margin-bottom:0.6rem">{_stars(score)}</div>
                <div style="color:rgba(255,255,255,0.5);font-size:0.88rem;font-style:italic">{reason}</div>
                {draft_html}
            </div>
            """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ═════════════════════════════════════════════════════════════════
def show_admin_view():
    # Top nav
    col_back, _ = st.columns([1, 8])
    with col_back:
        if st.button("← Home", key="btn_admin_back"):
            st.session_state.admin_authed = False
            _go(None)

    st.markdown('<p class="hero-title" style="font-size:2.4rem;margin-top:0.5rem">Admin Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Real-time insights powered by Groq AI</p>', unsafe_allow_html=True)

    # ── Fetch data
    with st.spinner("Loading data..."):
        try:
            summary_resp = requests.get(f"{API_BASE}/admin/summary", timeout=60)
            reviews_resp = requests.get(f"{API_BASE}/reviews", timeout=15)
        except requests.exceptions.ConnectionError:
            st.error("❌ **Cannot connect to the backend.** Make sure FastAPI is running:\n```\nuvicorn backend.main:app --reload\n```")
            return

    if summary_resp.status_code != 200:
        st.error(f"❌ Error fetching summary: {summary_resp.text}")
        return
    if reviews_resp.status_code != 200:
        st.error(f"❌ Error fetching reviews: {reviews_resp.text}")
        return

    summary = summary_resp.json()
    reviews = reviews_resp.json()

    # ── Metric row ────────────────────────────────────────────────
    st.markdown('<p class="section-header">Overview</p>', unsafe_allow_html=True)

    total = summary.get("total", 0)
    pos   = summary.get("positive_count", 0)
    neg   = summary.get("negative_count", 0)
    avg   = float(summary.get("avg_score") or 0)

    # Build the HTML as one string — no leading spaces so Markdown won't
    # treat it as a code block (4-space indent = code block in Markdown).
    _card = (
        '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:0.5rem;">'
        + '<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:1.3rem;">'
        + '<div style="color:rgba(255,255,255,0.65);font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Total Reviews</div>'
        + f'<div style="color:#ffffff;font-weight:800;font-size:2.2rem;line-height:1.1;">{total}</div>'
        + '</div>'
        + '<div style="background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.25);border-radius:16px;padding:1.3rem;">'
        + '<div style="color:rgba(255,255,255,0.65);font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Positive</div>'
        + f'<div style="color:#00d4aa;font-weight:800;font-size:2.2rem;line-height:1.1;">{pos}</div>'
        + '</div>'
        + '<div style="background:rgba(255,107,107,0.08);border:1px solid rgba(255,107,107,0.25);border-radius:16px;padding:1.3rem;">'
        + '<div style="color:rgba(255,255,255,0.65);font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Negative</div>'
        + f'<div style="color:#ff6b6b;font-weight:800;font-size:2.2rem;line-height:1.1;">{neg}</div>'
        + '</div>'
        + '<div style="background:rgba(245,166,35,0.08);border:1px solid rgba(245,166,35,0.25);border-radius:16px;padding:1.3rem;">'
        + '<div style="color:rgba(255,255,255,0.65);font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Avg Score</div>'
        + f'<div style="color:#f5a623;font-weight:800;font-size:2.2rem;line-height:1.1;">{avg:.1f} <span style="font-size:1rem;font-weight:400;color:rgba(255,255,255,0.4);">/ 5.0</span></div>'
        + '</div>'
        + '</div>'
    )
    st.markdown(_card, unsafe_allow_html=True)

    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)

    # ── LLM Insights ─────────────────────────────────────────────
    st.markdown('<p class="section-header">AI Insights</p>', unsafe_allow_html=True)

    pos_summary = summary.get("positive_summary", "—")
    neg_summary = summary.get("negative_summary", "—")

    st.markdown(f"""
    <div class="insight-positive">
        <div class="insight-label-pos">What customers love</div>
        <div class="insight-text">{pos_summary}</div>
    </div>
    <div class="insight-negative">
        <div class="insight-label-neg">Areas needing improvement</div>
        <div class="insight-text">{neg_summary}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)

    # ── Reviews table ─────────────────────────────────────────────
    st.markdown('<p class="section-header">All Reviews</p>', unsafe_allow_html=True)

    if not reviews:
        st.info("No reviews in the database yet. Ask customers to submit feedback, or run `python seed_db.py` to load sample data.")
        return

    df = pd.DataFrame(reviews)
    df["Stars"]     = df["score"].apply(_stars)
    df["Sentiment"] = df["sentiment"].apply(
        lambda s: "Positive" if s == "positive" else "Negative"
    )
    df["Date"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d  %H:%M")

    def _format_agent(row):
        parts = []
        if row.get("flagged") == 1:
            urgency = (row.get("urgency") or "high").upper()
            reason = row.get("flag_reason") or ""
            parts.append(f"🚩 FLAGGED ({urgency}): {reason}")
        if pd.notna(row.get("draft_response")) and row.get("draft_response"):
            parts.append(f"✍️ DRAFT: {row['draft_response']}")
        return "\n\n".join(parts) if parts else "—"
        
    df["Agent Actions"] = df.apply(_format_agent, axis=1)

    display_df = df[["review_text", "Sentiment", "Stars", "Agent Actions", "Date"]].rename(
        columns={"review_text": "Review"}
    )

    def _style_sentiment(val):
        if val == "Positive":
            return "background-color: rgba(0,212,170,0.2); color: #00d4aa; font-weight: 600;"
        elif val == "Negative":
            return "background-color: rgba(255,107,107,0.2); color: #ff6b6b; font-weight: 600;"
        return ""

    styled_df = display_df.style.map(_style_sentiment, subset=["Sentiment"])

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=420,
        hide_index=True,
    )


# ═════════════════════════════════════════════════════════════════
#  ROUTER
# ═════════════════════════════════════════════════════════════════
role = st.session_state.role

if role is None:
    show_landing()
elif role == "user":
    show_user_view()
elif role == "admin_login":
    show_admin_login()
elif role == "admin":
    if st.session_state.admin_authed:
        show_admin_view()
    else:
        show_admin_login()
