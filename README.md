# SkillMatch AI 🎯

> AI-powered career matching system — Resume parsing · Skill extraction · Job matching · Gap analysis · Career path prediction

![SkillMatch AI](https://img.shields.io/badge/SkillMatch-AI-00c2a8?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 Resume Parsing | PDF · DOCX · TXT via PyMuPDF & python-docx |
| 🧠 NLP Extraction | spaCy entity recognition + keyword taxonomy |
| 🔍 Job Matching | TF-IDF + cosine similarity against 30 curated jobs |
| 📊 Gap Analysis | Prioritised (required / high / nice) with course links |
| 🛤️ Career Path | 3-stage roadmap (Now → +6 weeks → +3 months) |
| 🔒 Local & Private | Everything runs on your machine |

---

## 🗂️ Project Structure

```
skillmatch-ai/
├── backend/
│   ├── main.py            # FastAPI app, all endpoints & logic
│   ├── requirements.txt   # Python dependencies
│   ├── database.db        # SQLite (auto-created on first run)
│   └── skillmatch.log     # Runtime logs (auto-created)
├── frontend/
│   ├── index.html         # Main HTML (no inline CSS/JS)
│   ├── styles.css         # All styles — dark glassmorphism
│   └── script.js          # All JS — API integration & rendering
└── README.md
```

---

## 🚀 Quick Start

### 1 · Clone or extract the project

```bash
cd skillmatch-ai
```

### 2 · Set up the Python backend

```bash
cd backend

# Create & activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (optional but enhances NLP)
python -m spacy download en_core_web_sm
```

### 3 · Start the backend

```bash
uvicorn main:app --reload
```

The API will be live at **http://127.0.0.1:8000**

- Swagger docs → http://127.0.0.1:8000/docs
- ReDoc → http://127.0.0.1:8000/redoc
- Health → http://127.0.0.1:8000/health

### 4 · Open the frontend

Open `frontend/index.html` in your browser.

> **Tip:** For a better experience (avoids CORS file:// issues), serve it:
> ```bash
> cd frontend
> python -m http.server 3000
> # Open http://localhost:3000
> ```

---

## 🔌 API Reference

### `GET /api/stats`
Returns platform statistics.
```json
{ "total_jobs": 30, "total_analyses": 42 }
```

### `POST /api/analyze/text`
Analyse a comma-separated or free-text skill list.

**Request:**
```json
{ "skills": "Python, Machine Learning, React, Docker" }
```

**Response:**
```json
{
  "extracted_skills": ["Python", "Machine Learning", "React", "Docker"],
  "matches": [
    {
      "id": 1,
      "title": "ML Engineer",
      "company": "Anthropic",
      "match_percent": 84,
      "salary": "$180k–$240k",
      "type": "Remote",
      "required_skills": ["Python", "PyTorch", ...],
      "matched_skills": ["Python", "Machine Learning"]
    }
  ],
  "gaps": [
    {
      "skill": "PyTorch",
      "priority": "required",
      "course": {
        "name": "PyTorch for Deep Learning",
        "provider": "fast.ai",
        "duration": "3 months",
        "level": "Advanced"
      }
    }
  ],
  "career_path": [
    {
      "stage": "Now",
      "title": "Junior ML Engineer",
      "timeframe": "Current",
      "description": "Build foundations in Python, Machine Learning...",
      "skills_to_gain": ["Python", "PyTorch", "TensorFlow"]
    }
  ]
}
```

### `POST /api/analyze/resume`
Upload a PDF, DOCX, or TXT resume file.

```bash
curl -X POST http://127.0.0.1:8000/api/analyze/resume \
  -F "file=@my_resume.pdf"
```

Returns same JSON structure as `/api/analyze/text`.

### `GET /health`
```json
{ "status": "healthy", "timestamp": "2024-01-01T12:00:00" }
```

---

## 🧠 How It Works

```
Resume / Skills
     │
     ▼
Text Extraction (PyMuPDF / python-docx)
     │
     ▼
NLP Skill Extraction (spaCy + keyword taxonomy)
     │
     ▼
TF-IDF Vectorisation (scikit-learn)
     │
     ▼
Cosine Similarity → Top 6 Job Matches
     │
     ▼
Gap Analysis (required / high / nice) + Courses
     │
     ▼
Career Path (Now → +6 weeks → +3 months)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| NLP | spaCy `en_core_web_sm` |
| Matching | scikit-learn TF-IDF + cosine similarity |
| PDF Parsing | PyMuPDF (fitz) |
| DOCX Parsing | python-docx |
| Database | SQLite |
| Frontend | Vanilla HTML · CSS · JavaScript |
| Fonts | Syne (headings) · DM Sans (body) |
| Design | Dark glassmorphism, navy/teal palette |

---

## ⚙️ Configuration

The backend is configured entirely in `main.py`:

- **`JOBS`** — 30 job listings with skills, salary, type
- **`COURSES`** — Course recommendations per skill
- **`SKILL_KEYWORDS`** — 80+ normalised skill keywords
- **`DB_PATH`** — SQLite path (default: `./database.db`)

The frontend API base URL is in `script.js`:
```js
const API = "http://127.0.0.1:8000";
```

Change this if deploying the backend to a different host.

---

## 📦 Dependencies

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
spacy>=3.7.0
scikit-learn>=1.4.0
pandas>=2.2.0
numpy>=1.26.0
python-multipart>=0.0.9
pymupdf>=1.24.0
python-docx>=1.1.0
pydantic>=2.0.0
```

> spaCy NLP is optional — the system falls back to pure keyword matching if `en_core_web_sm` is not installed.

---

## 🔒 Privacy

All analysis runs locally on your machine. No data is sent to external servers.

---

*Built with FastAPI · spaCy · scikit-learn · ❤️*
