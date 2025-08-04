from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF
import re
import torch

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load sentence transformer
model = SentenceTransformer("all-MiniLM-L6-v2")

class InputData(BaseModel):
    resume: str
    jd: str = ""

# ---------------- PDF Text Extraction ----------------
@app.post("/extract-text")
async def extract_text_from_pdf(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        extracted_text = ""

        for page in doc:
            # Use safe method: 'text' gives string
            text = page.get_text("text")
            if text:
                extracted_text += text + "\n"

        doc.close()

        if not extracted_text.strip():
            return {"error": "PDF looks empty. Try pasting text manually."}

        return {"text": extracted_text.strip()}

    except Exception as e:
        return {"error": f"Error reading PDF: {str(e)}"}

# ---------------- Resume Analysis ----------------
def get_embedding(text):
    return model.encode([text], convert_to_tensor=True)

def get_similarity(emb1, emb2):
    return torch.nn.functional.cosine_similarity(emb1, emb2).item()

def count_matching_keywords(resume, jd_keywords):
    resume = resume.lower()
    matched = {kw.lower() for kw in jd_keywords if kw and re.search(rf'\b{re.escape(kw)}\b', resume)}
    return len(matched)

def contains_action_verbs(text):
    verbs = ["led", "built", "created", "designed", "developed", "managed", "launched", "executed"]
    return sum(1 for v in verbs if re.search(rf"\b{v}\b", text.lower()))

def check_ats_safe(text):
    unsafe = any(tag in text.lower() for tag in ["<table", "<img", "columns:"])
    return not unsafe

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
        tailoring = get_similarity(resume_embed, jd_embed) * 30
    else:
        tailoring = 20
    score += tailoring

    # Skills match
    if jd:
        jd_keywords = re.findall(r'\b[a-zA-Z0-9+#]+\b', jd)
        matched = count_matching_keywords(resume, jd_keywords)
        skills_score = min(matched, 10) * 2
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
