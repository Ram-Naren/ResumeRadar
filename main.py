from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModel
import torch
import re
import fitz  # PyMuPDF
import language_tool_python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
tool = language_tool_python.LanguageTool('en-US')

class InputData(BaseModel):
    resume: str
    jd: str = ""

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)

def get_similarity(embedding1, embedding2):
    return torch.nn.functional.cosine_similarity(embedding1, embedding2).item()

def count_matching_keywords(resume, jd_keywords):
    resume_lower = resume.lower()
    matched = {kw.lower() for kw in jd_keywords if kw and re.search(rf'\b{re.escape(kw)}\b', resume_lower)}
    return len(matched)

def contains_action_verbs(text):
    action_verbs = ["led", "built", "created", "designed", "developed", "managed", "launched", "executed"]
    return sum(1 for verb in action_verbs if re.search(rf"\b{verb}\b", text.lower()))

def check_ats_safe_design(text):
    html_like = any(tag in text.lower() for tag in ["<table", "<img"])
    columns_flag = bool(re.search(r'columns?[:\-]', text.lower()))
    return not (html_like or columns_flag)

def check_grammar(text):
    return tool.check(text)

def check_structure(text):
    required_sections = [
        r'education|academic',
        r'(work|professional)\s+(experience|history)',
        r'(technical\s+)?skills',
        r'project[s]?',
        r'(contact|email|phone)'
    ]
    return sum(1 for sec in required_sections if re.search(sec, text.lower()))

def check_bonus(text):
    bonus = 0
    text_lower = text.lower()
    if "project" in text_lower:
        bonus += 1
    if "internship" in text_lower:
        bonus += 1
    if re.search(r'\b(\d+%|\$\d+|reduced\s+\d+%)\b', text_lower):
        bonus += 1
    return bonus

@app.post("/analyze")
async def analyze(data: InputData):
    resume_text = data.resume.strip()
    jd_text = data.jd.strip()

    if not resume_text:
        return {"score": 0.0, "suggestions": ["Resume is empty."]}

    total_score = 0
    suggestions = []

    # Tailoring (with fallback)
    if jd_text:
        resume_embed = get_embedding(resume_text)
        jd_embed = get_embedding(jd_text)
        tailoring_score = get_similarity(resume_embed, jd_embed) * 30
    else:
        tailoring_score = 20  # safer default
    total_score += tailoring_score

    # Skills Match (only if JD present)
    if jd_text:
        jd_keywords = re.findall(r'\b[a-zA-Z0-9+#]+\b', jd_text)
        skills_score = min(count_matching_keywords(resume_text, jd_keywords), 10) * 2
        if skills_score < 10:
            suggestions.append("Match more relevant keywords from the job description.")
    else:
        skills_score = 15
    total_score += skills_score

    # Action Verbs
    action_score = min(contains_action_verbs(resume_text), 10)
    if action_score < 3:
        suggestions.append("Add more action verbs to describe your achievements.")
    total_score += action_score

    # ATS Design
    ats_safe = check_ats_safe_design(resume_text)
    ats_score = 10 if ats_safe else 0
    if not ats_safe:
        suggestions.append("Resume may contain unsafe design elements (like tables or columns).")
    total_score += ats_score

    # Grammar Check
    grammar_issues = check_grammar(resume_text)
    grammar_score = max(0, 10 - len(grammar_issues))
    if grammar_issues:
        suggestions.append(f"Found {len(grammar_issues)} grammar/spelling issue(s):")
        for issue in grammar_issues[:3]:
            suggestions.append(f"- {issue.message} → \"{issue.context}\"")
    total_score += grammar_score

    # Structure Check
    structure_score = min(check_structure(resume_text), 5) * 2
    if structure_score < 10:
        suggestions.append("Include standard sections like Education, Experience, Skills, Projects.")
    total_score += structure_score

    # Bonus
    bonus_score = check_bonus(resume_text) * 3.33
    total_score += bonus_score

    return {
        "score": round(total_score, 2),
        "out_of": 100,
        "suggestions": suggestions
    }

@app.post("/extract-text")
async def extract_text_from_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported."}

    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return {"text": text}
