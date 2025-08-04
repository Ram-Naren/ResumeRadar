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

# Load once to avoid memory waste
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()  # No need to train

# Use in-memory tool instance
tool = language_tool_python.LanguageTool('en-US')

class InputData(BaseModel):
    resume: str
    jd: str = ""

def get_embedding(text: str) -> torch.Tensor:
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)

def get_similarity(embed1, embed2):
    return torch.nn.functional.cosine_similarity(embed1, embed2).item()

def count_matching_keywords(resume: str, jd_keywords):
    resume_lower = resume.lower()
    return sum(1 for kw in jd_keywords if kw and re.search(rf'\b{re.escape(kw.lower())}\b', resume_lower))

def contains_action_verbs(text: str):
    verbs = ["led", "built", "created", "designed", "developed", "managed", "launched", "executed"]
    return sum(bool(re.search(rf"\\b{verb}\\b", text.lower())) for verb in verbs)

def check_ats_safe_design(text: str):
    text_lower = text.lower()
    return not ("<table" in text_lower or "<img" in text_lower or re.search(r'columns?[:\-]', text_lower))

def check_grammar(text: str):
    return len(tool.check(text))

def check_structure(text: str):
    sections = [r'education', r'(work\s+)?experience', r'skills', r'project[s]?', r'contact|email|phone']
    return sum(bool(re.search(sec, text.lower())) for sec in sections)

def check_bonus(text: str):
    text_lower = text.lower()
    bonus = 0
    if "project" in text_lower: bonus += 1
    if "internship" in text_lower: bonus += 1
    if re.search(r'\b(\d+%|\$\d+|reduced\s+\d+%)\b', text_lower): bonus += 1
    return bonus

@app.post("/analyze")
async def analyze(data: InputData):
    resume_text, jd_text = data.resume.strip(), data.jd.strip()

    if not resume_text:
        return {"score": 0.0, "suggestions": ["Resume is empty."]}

    total_score = 0
    suggestions = []

    # Tailoring (semantic similarity)
    if jd_text:
        tailoring_score = get_similarity(get_embedding(resume_text), get_embedding(jd_text)) * 30
    else:
        tailoring_score = 20
    total_score += tailoring_score

    # Skills Match
    if jd_text:
        keywords = re.findall(r'\b[a-zA-Z0-9+#]+\b', jd_text)
        match_score = min(count_matching_keywords(resume_text, keywords), 10) * 2
        if match_score < 10:
            suggestions.append("Match more relevant keywords from the job description.")
    else:
        match_score = 15
    total_score += match_score

    # Action Verbs
    action_score = min(contains_action_verbs(resume_text), 10)
    if action_score < 3:
        suggestions.append("Add more action verbs to describe your achievements.")
    total_score += action_score

    # ATS Safety
    ats_score = 10 if check_ats_safe_design(resume_text) else 0
    if ats_score == 0:
        suggestions.append("Resume may contain unsafe design elements (like tables or columns).")
    total_score += ats_score

    # Grammar
    grammar_issues = check_grammar(resume_text)
    grammar_score = max(0, 10 - grammar_issues)
    if grammar_issues > 0:
        suggestions.append(f"Found {grammar_issues} grammar/spelling issue(s).")
    total_score += grammar_score

    # Structure
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
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return {"text": text}
