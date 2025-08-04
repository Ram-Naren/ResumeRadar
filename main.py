from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF
import numpy as np
import re

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = SentenceTransformer("all-MiniLM-L6-v2")  # RAM-friendly

class InputData(BaseModel):
    resume: str
    jd: str = ""

# --------- PDF Extraction ---------
@app.post("/extract-text")
async def extract_text_from_pdf(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        extracted_text = ""

        for page in doc:
            text = page.get_text("text")
            if text:
                extracted_text += text + "\n"
        doc.close()

        if not extracted_text.strip():
            return {"error": "PDF appears empty or unreadable."}
        return {"text": extracted_text.strip()}
    except Exception as e:
        return {"error": f"Error reading PDF: {str(e)}"}


# --------- Resume Analysis ---------
def get_embedding(text):
    return model.encode(text)

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot = np.dot(vec1, vec2)
    norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    return float(dot / norm) if norm != 0 else 0.0

def count_matching_keywords(resume, jd_keywords):
    resume = resume.lower()
    return sum(1 for kw in jd_keywords if re.search(rf'\b{re.escape(kw.lower())}\b', resume))

def contains_action_verbs(text):
    verbs = ["led", "built", "created", "designed", "developed", "managed", "launched", "executed"]
    return sum(1 for v in verbs if re.search(rf"\b{v}\b", text.lower()))

def check_ats_safe(text):
    return not any(tag in text.lower() for tag in ["<table", "<img", "columns:"])

def check_structure(text):
    sections = [r'education|academic', r'work\s+experience', r'skills', r'projects?', r'contact|email|phone']
    return sum(1 for sec in sections if re.search(sec, text.lower()))

def check_bonus(text):
    t = text.lower()
    score = 0
    if "project" in t: score += 1
    if "internship" in t: score += 1
    if re.search(r'\b(\d+%|\$\d+|reduced\s+\d+%)\b', t): score += 1
    return score

@app.post("/analyze")
async def analyze(data: InputData):
    resume = data.resume.strip()
    jd = data.jd.strip()

    if not resume:
        return {"score": 0.0, "suggestions": ["Resume is empty."]}

    score = 0
    suggestions = []

    # Tailoring
    if jd:
        resume_embed = get_embedding(resume)
        jd_embed = get_embedding(jd)
        tailoring = cosine_similarity(resume_embed, jd_embed) * 30
    else:
        tailoring = 20
    score += tailoring

    # Skills match
    if jd:
        jd_keywords = re.findall(r'\b[a-zA-Z0-9+#]+\b', jd)
        skills_score = min(count_matching_keywords(resume, jd_keywords), 10) * 2
        if skills_score < 10:
            suggestions.append("Match more keywords from the job description.")
    else:
        skills_score = 15
    score += skills_score

    # Action verbs
    action_score = min(contains_action_verbs(resume), 10)
    if action_score < 3:
        suggestions.append("Add more action verbs like 'developed', 'managed', etc.")
    score += action_score

    # ATS safe
    ats_score = 10 if check_ats_safe(resume) else 0
    if ats_score == 0:
        suggestions.append("Avoid using tables, columns or images in resume.")
    score += ats_score

    # Structure
    structure_score = min(check_structure(resume), 5) * 2
    if structure_score < 10:
        suggestions.append("Include sections like Education, Projects, Skills, etc.")
    score += structure_score

    # Bonus
    score += check_bonus(resume) * 3.33

    return {
        "score": round(score, 2),
        "out_of": 100,
        "suggestions": suggestions
    }
