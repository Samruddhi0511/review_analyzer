# 🍽️ Customer Feedback Analyzer

An end-to-end AI-powered restaurant review analysis system. Customers submit reviews and instantly get sentiment analysis. Negative reviews are handed off to an **agent** that decides what to do about them. Admins get a full dashboard with AI-generated insights powered by **Groq LLM**.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | [Streamlit](https://streamlit.io/) |
| Backend | [FastAPI](https://fastapi.tiangolo.com/) |
| Database | SQLite |
| AI / LLM | [Groq](https://console.groq.com) (`llama-3.3-70b-versatile`) |

---

## ✨ Features

### 👤 Customer View
- Submit a restaurant review via a clean text form
- Instantly see AI-analyzed **sentiment** (Positive / Negative)
- Get a **score out of 5** and a short reason from the LLM

### 🤖 Negative Review Agent
When a review comes back negative, a small agent takes over and decides — on its own, using tool calling — what should happen next:
- **Flags it for a manager** if the issue is serious (e.g. safety, rude staff), with an urgency level and reason
- **Drafts a customer-facing response** in an appropriate tone
- **Checks the database for repeat complaints** (e.g. "cold food" mentioned 3+ times this week) and surfaces it as a trend

The agent can call more than one tool per review, and it's judgment-based — not every negative review gets escalated, only the ones that warrant it.

### 🔐 Admin Dashboard (password protected)
- **Stats cards** — Total reviews, Positive count, Negative count, Avg score
- **AI Insights** — One-line LLM summary of what positive reviews praise and what negative reviews complain about
- **Full reviews table** — All reviews with color-coded sentiment, star rating, and date
- **Agent actions** — What the agent decided to do about each negative review (flagged / drafted a response / trend detected)

---

## 📁 Project Structure

```
Customer_feedback_analyzer/
├── backend/
│   ├── __init__.py
│   ├── database.py      # SQLite setup & queries
│   ├── llm.py           # Groq API integration (sentiment + summaries)
│   ├── agents.py         # Negative-review agent (tool calling: flag, draft, trend-check)
│   ├── models.py        # Pydantic request/response models
│   └── main.py          # FastAPI routes
├── frontend/
│   └── app.py           # Streamlit UI
├── seed_db.py           # Load sample reviews into DB
├── sample_reviews.txt   # 20 sample restaurant reviews
├── requirements.txt
├── .env                 # API key (create this yourself, not committed)
└── .gitignore
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/Customer_feedback_analyzer.git
cd Customer_feedback_analyzer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a Groq API key
Sign up for free at [console.groq.com](https://console.groq.com), go to **API Keys**, and create a new key.

### 4. Create your `.env` file
Create a file named `.env` in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```
> ⚠️ Never commit this file. It's already in `.gitignore`.

---

## 🚀 Running the App

You need **two terminals** open in the project folder.

### Terminal 1 — Start the FastAPI backend
```bash
uvicorn backend.main:app --reload
```
Backend will run at `http://localhost:8000`

### Terminal 2 — Start the Streamlit frontend
```bash
streamlit run frontend/app.py
```
App will open at `http://localhost:8501`

### (Optional) Seed sample data
With the backend running, load the 20 sample reviews:
```bash
python seed_db.py
```
This sends each review through the LLM for analysis and stores them in the DB. Takes ~30–60 seconds.

---

## 🔌 API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/reviews` | Submit a review → LLM analysis → agent runs if negative → saved to DB |
| `GET` | `/reviews` | Get all reviews |
| `GET` | `/admin/summary` | Stats + LLM-generated insights |

Interactive API docs available at `http://localhost:8000/docs`

---

## 🔐 Admin Login

Default password: **`admin123`**

To change it, update this line in `frontend/app.py`:
```python
ADMIN_PASSWORD = "admin123"
```
> ⚠️ This is hardcoded for demo purposes. In production, this should be hashed and stored outside the source code (e.g. an environment variable).

---

## 📊 How It Works

```
Customer types review in Streamlit
        ↓
POST /reviews → FastAPI receives it
        ↓
Groq LLM analyzes: sentiment + score (1–5) + reason
        ↓
Stored in SQLite database
        ↓
If sentiment is Negative:
        ↓
Agent (agents.py) decides which tool(s) to call:
   • flag_for_manager_review  — escalate serious issues
   • draft_response           — write a reply
   • check_repeat_complaint   — query DB for a trend
        ↓
Agent's actions stored + shown to customer/admin instantly

Admin opens dashboard
        ↓
GET /admin/summary → FastAPI fetches all reviews
        ↓
Groq LLM generates insight summaries
        ↓
Stats + AI insights + agent actions + full table displayed
```

---

## 📦 Requirements

```
fastapi
uvicorn[standard]
streamlit
groq
python-dotenv
requests
pandas
```

---

## 📄 License

MIT License — feel free to use, modify, and share.