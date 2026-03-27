"""
SkillMatch AI - Backend API
FastAPI + spaCy + scikit-learn powered career matching system
"""

import logging
import io
import re
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("skillmatch.log"),
    ],
)
logger = logging.getLogger("skillmatch")

# ── App Setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SkillMatch AI",
    description="AI-powered career matching system with resume parsing and skill gap analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database ────────────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent / "database.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_type TEXT,
            skills_extracted TEXT,
            top_match TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialised")


init_db()

# ── Job Dataset ─────────────────────────────────────────────────────────────────
JOBS = [
    {"id": 1, "title": "ML Engineer", "company": "Anthropic", "skills": ["Python", "PyTorch", "TensorFlow", "Machine Learning", "Deep Learning", "NLP", "Git", "Docker"], "salary": "$180k–$240k", "type": "Remote"},
    {"id": 2, "title": "Data Scientist", "company": "Google DeepMind", "skills": ["Python", "R", "Statistics", "Machine Learning", "SQL", "Pandas", "NumPy", "Visualization"], "salary": "$160k–$210k", "type": "Hybrid"},
    {"id": 3, "title": "Full Stack Engineer", "company": "Stripe", "skills": ["React", "Node.js", "TypeScript", "PostgreSQL", "REST API", "Docker", "AWS", "Git"], "salary": "$150k–$200k", "type": "Remote"},
    {"id": 4, "title": "AI Research Scientist", "company": "OpenAI", "skills": ["Python", "PyTorch", "Mathematics", "Deep Learning", "Research", "NLP", "Statistics", "CUDA"], "salary": "$200k–$280k", "type": "On-site"},
    {"id": 5, "title": "DevOps Engineer", "company": "HashiCorp", "skills": ["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD", "Linux", "Python", "Monitoring"], "salary": "$140k–$180k", "type": "Remote"},
    {"id": 6, "title": "Backend Engineer", "company": "Notion", "skills": ["Python", "Go", "PostgreSQL", "Redis", "REST API", "Microservices", "Docker", "Kafka"], "salary": "$145k–$190k", "type": "Hybrid"},
    {"id": 7, "title": "Frontend Engineer", "company": "Figma", "skills": ["React", "TypeScript", "CSS", "JavaScript", "WebGL", "Performance", "Accessibility", "Design Systems"], "salary": "$135k–$175k", "type": "Hybrid"},
    {"id": 8, "title": "Data Engineer", "company": "Databricks", "skills": ["Python", "Spark", "SQL", "Airflow", "dbt", "AWS", "Kafka", "Data Warehousing"], "salary": "$150k–$195k", "type": "Remote"},
    {"id": 9, "title": "Cloud Architect", "company": "AWS", "skills": ["AWS", "Azure", "Terraform", "Kubernetes", "Architecture", "Security", "Networking", "Python"], "salary": "$170k–$220k", "type": "Hybrid"},
    {"id": 10, "title": "NLP Engineer", "company": "Cohere", "skills": ["Python", "NLP", "Transformers", "PyTorch", "BERT", "spaCy", "Machine Learning", "APIs"], "salary": "$155k–$200k", "type": "Remote"},
    {"id": 11, "title": "Security Engineer", "company": "Crowdstrike", "skills": ["Security", "Python", "Network Security", "Penetration Testing", "Linux", "SIEM", "Cryptography"], "salary": "$140k–$185k", "type": "Remote"},
    {"id": 12, "title": "Product Data Analyst", "company": "Airbnb", "skills": ["SQL", "Python", "A/B Testing", "Statistics", "Tableau", "Product Analytics", "Excel"], "salary": "$120k–$160k", "type": "Hybrid"},
    {"id": 13, "title": "Robotics Engineer", "company": "Boston Dynamics", "skills": ["C++", "Python", "ROS", "Control Systems", "Computer Vision", "Kinematics", "SLAM"], "salary": "$145k–$190k", "type": "On-site"},
    {"id": 14, "title": "iOS Developer", "company": "Apple", "skills": ["Swift", "SwiftUI", "Objective-C", "Xcode", "CoreData", "ARKit", "Performance", "UIKit"], "salary": "$150k–$200k", "type": "On-site"},
    {"id": 15, "title": "Android Developer", "company": "Google", "skills": ["Kotlin", "Java", "Android SDK", "Jetpack Compose", "Firebase", "REST API", "CI/CD"], "salary": "$145k–$195k", "type": "Hybrid"},
    {"id": 16, "title": "MLOps Engineer", "company": "Weights & Biases", "skills": ["Python", "MLflow", "Docker", "Kubernetes", "Machine Learning", "CI/CD", "AWS", "Monitoring"], "salary": "$155k–$200k", "type": "Remote"},
    {"id": 17, "title": "Quantitative Analyst", "company": "Jane Street", "skills": ["Python", "R", "Statistics", "Mathematics", "Machine Learning", "Finance", "C++", "Optimization"], "salary": "$200k–$350k", "type": "On-site"},
    {"id": 18, "title": "Site Reliability Engineer", "company": "Meta", "skills": ["Linux", "Python", "Kubernetes", "Monitoring", "Incident Response", "Distributed Systems", "Go"], "salary": "$160k–$210k", "type": "Hybrid"},
    {"id": 19, "title": "Computer Vision Engineer", "company": "Tesla", "skills": ["Python", "Computer Vision", "PyTorch", "OpenCV", "Deep Learning", "C++", "CUDA", "Image Processing"], "salary": "$165k–$215k", "type": "On-site"},
    {"id": 20, "title": "Blockchain Developer", "company": "Coinbase", "skills": ["Solidity", "Web3.js", "Ethereum", "Python", "JavaScript", "Smart Contracts", "DeFi", "TypeScript"], "salary": "$140k–$195k", "type": "Remote"},
    {"id": 21, "title": "Platform Engineer", "company": "Spotify", "skills": ["Python", "Go", "Kubernetes", "Terraform", "GCP", "Microservices", "Kafka", "Docker"], "salary": "$145k–$190k", "type": "Hybrid"},
    {"id": 22, "title": "AR/VR Developer", "company": "Meta Reality Labs", "skills": ["Unity", "C#", "Unreal Engine", "C++", "3D Math", "OpenXR", "Shader Programming"], "salary": "$150k–$200k", "type": "Hybrid"},
    {"id": 23, "title": "Staff Software Engineer", "company": "Netflix", "skills": ["Java", "Python", "Distributed Systems", "Architecture", "Leadership", "Microservices", "AWS"], "salary": "$250k–$400k", "type": "Hybrid"},
    {"id": 24, "title": "Embedded Systems Engineer", "company": "NVIDIA", "skills": ["C", "C++", "CUDA", "Embedded Linux", "RTOS", "GPU Programming", "Assembly", "Hardware"], "salary": "$155k–$210k", "type": "On-site"},
    {"id": 25, "title": "Growth Data Scientist", "company": "Duolingo", "skills": ["Python", "SQL", "A/B Testing", "Causal Inference", "Statistics", "Bayesian Analysis", "Experimentation"], "salary": "$130k–$175k", "type": "Remote"},
    {"id": 26, "title": "Prompt Engineer", "company": "Scale AI", "skills": ["NLP", "Python", "LLMs", "Prompt Engineering", "Evaluation", "Data Annotation", "Machine Learning"], "salary": "$120k–$165k", "type": "Remote"},
    {"id": 27, "title": "Database Engineer", "company": "PlanetScale", "skills": ["MySQL", "PostgreSQL", "SQL", "Database Design", "Performance Tuning", "Go", "Vitess", "Sharding"], "salary": "$140k–$185k", "type": "Remote"},
    {"id": 28, "title": "API Platform Engineer", "company": "Twilio", "skills": ["Python", "Go", "REST API", "GraphQL", "Developer Experience", "Documentation", "TypeScript", "OpenAPI"], "salary": "$135k–$175k", "type": "Remote"},
    {"id": 29, "title": "Data Infrastructure Lead", "company": "Snowflake", "skills": ["SQL", "Python", "dbt", "Data Warehousing", "Snowflake", "Architecture", "Leadership", "ETL"], "salary": "$165k–$220k", "type": "Hybrid"},
    {"id": 30, "title": "AI Safety Researcher", "company": "Anthropic", "skills": ["Python", "Machine Learning", "Research", "Mathematics", "NLP", "Philosophy", "Statistics", "Deep Learning"], "salary": "$190k–$260k", "type": "Hybrid"},
]

# ── Course Dataset ──────────────────────────────────────────────────────────────
COURSES = {
    "Python": {"name": "Python for Everybody", "provider": "Coursera / U-Michigan", "duration": "3 months", "level": "Beginner"},
    "Machine Learning": {"name": "Machine Learning Specialization", "provider": "Coursera / DeepLearning.AI", "duration": "4 months", "level": "Intermediate"},
    "Deep Learning": {"name": "Deep Learning Specialization", "provider": "Coursera / DeepLearning.AI", "duration": "5 months", "level": "Advanced"},
    "React": {"name": "React - The Complete Guide", "provider": "Udemy", "duration": "6 weeks", "level": "Intermediate"},
    "Docker": {"name": "Docker & Kubernetes: The Practical Guide", "provider": "Udemy", "duration": "4 weeks", "level": "Intermediate"},
    "AWS": {"name": "AWS Solutions Architect Associate", "provider": "A Cloud Guru", "duration": "3 months", "level": "Intermediate"},
    "SQL": {"name": "SQL for Data Analysis", "provider": "Udacity", "duration": "6 weeks", "level": "Beginner"},
    "Kubernetes": {"name": "Certified Kubernetes Administrator", "provider": "Linux Foundation", "duration": "3 months", "level": "Advanced"},
    "NLP": {"name": "Natural Language Processing Specialization", "provider": "Coursera / DeepLearning.AI", "duration": "4 months", "level": "Advanced"},
    "TypeScript": {"name": "TypeScript: The Complete Developer's Guide", "provider": "Udemy", "duration": "4 weeks", "level": "Intermediate"},
    "PyTorch": {"name": "PyTorch for Deep Learning", "provider": "fast.ai", "duration": "3 months", "level": "Advanced"},
    "Statistics": {"name": "Statistics with Python Specialization", "provider": "Coursera / U-Michigan", "duration": "4 months", "level": "Intermediate"},
    "Terraform": {"name": "HashiCorp Terraform Associate", "provider": "HashiCorp", "duration": "6 weeks", "level": "Intermediate"},
    "Go": {"name": "Go Programming (Golang)", "provider": "Udemy", "duration": "5 weeks", "level": "Intermediate"},
}

# ── Skill Taxonomy ──────────────────────────────────────────────────────────────
SKILL_KEYWORDS = [
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
    "swift", "kotlin", "r", "scala", "ruby", "php", "dart", "solidity",
    "react", "vue", "angular", "node.js", "nodejs", "express", "nextjs",
    "django", "flask", "fastapi", "spring", "rails", "laravel",
    "postgresql", "mysql", "sqlite", "mongodb", "redis", "cassandra", "dynamodb",
    "machine learning", "deep learning", "nlp", "computer vision", "reinforcement learning",
    "pytorch", "tensorflow", "keras", "scikit-learn", "hugging face", "transformers",
    "docker", "kubernetes", "terraform", "ansible", "jenkins", "github actions",
    "aws", "gcp", "azure", "cloud", "serverless", "lambda",
    "sql", "nosql", "data warehousing", "etl", "airflow", "spark", "kafka", "dbt",
    "git", "linux", "bash", "ci/cd", "devops", "agile", "scrum",
    "rest api", "graphql", "microservices", "distributed systems",
    "statistics", "mathematics", "data analysis", "visualization", "tableau", "power bi",
    "pandas", "numpy", "matplotlib", "seaborn", "plotly",
    "openai", "llm", "bert", "gpt", "prompt engineering", "rag", "langchain",
    "security", "cryptography", "penetration testing", "network security",
    "mlops", "mlflow", "weights and biases", "wandb", "experiment tracking",
    "cuda", "gpu programming", "high performance computing",
    "unity", "unreal engine", "webgl", "three.js",
    "a/b testing", "causal inference", "bayesian",
    "leadership", "architecture", "system design", "research",
    "excel", "powerpoint", "product management", "communication",
    "html", "css", "web development", "responsive design",
]


def extract_skills_nlp(text: str) -> List[str]:
    """
    Extract skills from text using keyword matching with normalisation.
    Falls back gracefully if spaCy is unavailable.
    """
    text_lower = text.lower()
    found = []

    # Direct keyword matching (robust fallback)
    for skill in SKILL_KEYWORDS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill.title())

    # Try spaCy enrichment
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        for token in doc:
            if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 2:
                if token.text.lower() in SKILL_KEYWORDS and token.text.title() not in found:
                    found.append(token.text.title())
    except Exception:
        pass  # spaCy optional

    # Deduplicate (case-insensitive)
    seen, unique = set(), []
    for s in found:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


def compute_match(user_skills: List[str], job_skills: List[str]) -> float:
    """Cosine similarity via TF-IDF."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        user_str = " ".join(user_skills).lower()
        job_str = " ".join(job_skills).lower()
        if not user_str.strip():
            return 0.0
        vect = TfidfVectorizer(analyzer="word", ngram_range=(1, 2))
        mat = vect.fit_transform([user_str, job_str])
        score = cosine_similarity(mat[0], mat[1])[0][0]
        return round(float(score), 4)
    except Exception:
        # Simple Jaccard fallback
        u = set(s.lower() for s in user_skills)
        j = set(s.lower() for s in job_skills)
        if not u or not j:
            return 0.0
        return round(len(u & j) / len(u | j), 4)


def build_matches(user_skills: List[str]) -> List[dict]:
    results = []
    for job in JOBS:
        score = compute_match(user_skills, job["skills"])
        pct = min(round(score * 100 + np.random.uniform(2, 12)), 99)
        matched = [s for s in job["skills"] if any(s.lower() == u.lower() for u in user_skills)]
        results.append({
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "match_percent": pct,
            "salary": job["salary"],
            "type": job["type"],
            "required_skills": job["skills"],
            "matched_skills": matched,
        })
    results.sort(key=lambda x: x["match_percent"], reverse=True)
    return results[:6]


def build_gaps(user_skills: List[str], top_matches: List[dict]) -> List[dict]:
    if not top_matches:
        return []
    top_job = top_matches[0]
    user_lower = {s.lower() for s in user_skills}
    gaps = []
    for i, skill in enumerate(top_job["required_skills"]):
        if skill.lower() not in user_lower:
            priority = "required" if i < 3 else ("high" if i < 5 else "nice")
            course = COURSES.get(skill, {
                "name": f"Learn {skill}",
                "provider": "Various Platforms",
                "duration": "4–8 weeks",
                "level": "Intermediate",
            })
            gaps.append({
                "skill": skill,
                "priority": priority,
                "course": course,
            })
    return gaps[:8]


def build_career_path(user_skills: List[str], top_matches: List[dict]) -> List[dict]:
    top_title = top_matches[0]["title"] if top_matches else "Software Engineer"
    top_company = top_matches[0]["company"] if top_matches else "Top Tech"
    level_words = ["Junior", "Mid-level", "Senior", "Lead", "Principal"]

    base = top_title.replace("Senior ", "").replace("Staff ", "").replace("Lead ", "")
    return [
        {
            "stage": "Now",
            "title": f"Junior {base}",
            "timeframe": "Current",
            "description": f"Build foundations in {', '.join(user_skills[:3]) if user_skills else 'core skills'}.",
            "skills_to_gain": top_matches[0]["required_skills"][:3] if top_matches else [],
        },
        {
            "stage": "+6 Weeks",
            "title": base,
            "timeframe": "6 weeks",
            "description": f"Fill identified skill gaps and contribute to real projects at {top_company}.",
            "skills_to_gain": top_matches[0]["required_skills"][3:5] if top_matches else [],
        },
        {
            "stage": "+3 Months",
            "title": f"Senior {base}",
            "timeframe": "3 months",
            "description": f"Lead initiatives, mentor peers, and reach {top_matches[0]['salary'] if top_matches else '$150k+'} compensation.",
            "skills_to_gain": top_matches[0]["required_skills"][5:7] if top_matches else [],
        },
    ]


def log_analysis(input_type: str, skills: List[str], top_match: str):
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO analyses (input_type, skills_extracted, top_match, created_at) VALUES (?,?,?,?)",
            (input_type, json.dumps(skills), top_match, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"DB log failed: {e}")


# ── Models ──────────────────────────────────────────────────────────────────────
class TextAnalysisRequest(BaseModel):
    skills: str


# ── Endpoints ───────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "ok", "app": "SkillMatch AI", "version": "1.0.0"}


@app.get("/api/stats")
async def get_stats():
    try:
        conn = get_db()
        row = conn.execute("SELECT COUNT(*) as cnt FROM analyses").fetchone()
        count = row["cnt"] if row else 0
        conn.close()
    except Exception:
        count = 0
    return {
        "total_jobs": len(JOBS),
        "total_analyses": count,
    }


@app.post("/api/analyze/text")
async def analyze_text(req: TextAnalysisRequest):
    logger.info(f"Text analysis request: {req.skills[:80]}")
    if not req.skills.strip():
        raise HTTPException(status_code=400, detail="Skills field is empty")

    skills = extract_skills_nlp(req.skills)
    if not skills:
        # Parse comma-separated list directly
        skills = [s.strip().title() for s in req.skills.split(",") if s.strip()]

    matches = build_matches(skills)
    gaps = build_gaps(skills, matches)
    path = build_career_path(skills, matches)
    top = matches[0]["title"] if matches else "N/A"
    log_analysis("text", skills, top)
    logger.info(f"Extracted {len(skills)} skills, top match: {top}")

    return {
        "extracted_skills": skills,
        "matches": matches,
        "gaps": gaps,
        "career_path": path,
    }


@app.post("/api/analyze/resume")
async def analyze_resume(file: UploadFile = File(...)):
    logger.info(f"Resume upload: {file.filename} ({file.content_type})")
    content = await file.read()
    filename = (file.filename or "").lower()
    text = ""

    if filename.endswith(".pdf"):
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
        except ImportError:
            raise HTTPException(status_code=500, detail="PyMuPDF not installed. Run: pip install pymupdf")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF parse error: {e}")

    elif filename.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            raise HTTPException(status_code=500, detail="python-docx not installed")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DOCX parse error: {e}")

    elif filename.endswith(".txt") or file.content_type == "text/plain":
        text = content.decode("utf-8", errors="ignore")

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload PDF, DOCX, or TXT.")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    skills = extract_skills_nlp(text)
    matches = build_matches(skills)
    gaps = build_gaps(skills, matches)
    path = build_career_path(skills, matches)
    top = matches[0]["title"] if matches else "N/A"
    log_analysis("resume", skills, top)
    logger.info(f"Resume parsed: {len(skills)} skills, top match: {top}")

    return {
        "extracted_skills": skills,
        "matches": matches,
        "gaps": gaps,
        "career_path": path,
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
