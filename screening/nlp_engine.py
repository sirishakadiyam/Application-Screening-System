import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer


# ✅ Recommended model
MODEL_NAME = "BAAI/bge-base-en-v1.5"
# Alternatives:
# MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# MODEL_NAME = "intfloat/e5-large-v2"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def clean_text(t: str) -> str:
    t = t or ""
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_text_from_resume(uploaded_file) -> str:
    """
    Supports PDF, DOCX, TXT
    """
    name = (uploaded_file.name or "").lower()

    if name.endswith(".pdf"):
        return _extract_pdf(uploaded_file)
    if name.endswith(".docx"):
        return _extract_docx(uploaded_file)
    if name.endswith(".txt"):
        return _extract_txt(uploaded_file)

    raise ValueError("Unsupported file type. Please upload PDF, DOCX, or TXT.")


def _extract_txt(uploaded_file):
    uploaded_file.seek(0)
    content = uploaded_file.read()
    uploaded_file.seek(0)
    return content.decode("utf-8", errors="ignore")


def _extract_pdf(uploaded_file):
    import pdfplumber
    uploaded_file.seek(0)
    text_parts = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    uploaded_file.seek(0)
    return "\n".join(text_parts)


def _extract_docx(uploaded_file):
    from docx import Document
    uploaded_file.seek(0)
    doc = Document(uploaded_file)
    paras = [p.text for p in doc.paragraphs if p.text.strip()]
    uploaded_file.seek(0)
    return "\n".join(paras)


def semantic_similarity(job_desc: str, resume_text: str) -> float:
    """
    Embedding-based cosine similarity (0..100)
    """
    model = get_model()
    jd = clean_text(job_desc)
    rs = clean_text(resume_text)

    if not jd or not rs:
        return 0.0

    embeddings = model.encode([jd, rs], normalize_embeddings=True)
    score = float(np.dot(embeddings[0], embeddings[1]))

    score_0_100 = max(0.0, min(100.0, (score + 1.0) * 50.0))
    return round(score_0_100, 2)


def extract_top_keywords(job_desc: str, top_k=20):
    jd = clean_text(job_desc).lower()
    if not jd:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=3000
    )
    X = vectorizer.fit_transform([jd])
    terms = vectorizer.get_feature_names_out()
    scores = X.toarray()[0]

    ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
    keywords = [t for t, s in ranked if s > 0][:top_k]
    keywords = [k for k in keywords if len(k) >= 3 and not k.isdigit()]
    return keywords


def missing_keywords(job_keywords, resume_text):
    rs = clean_text(resume_text).lower()
    missing = [kw for kw in job_keywords if kw.lower() not in rs]
    return missing


def section_check(resume_text):
    t = resume_text.lower()
    required = {
        "Skills": ["skills", "technical skills", "core competencies"],
        "Experience": ["experience", "work experience", "employment"],
        "Education": ["education", "academic"],
        "Projects": ["projects", "project experience"],
    }
    missing = []
    for section, cues in required.items():
        if not any(cue in t for cue in cues):
            missing.append(section)
    return missing


def improvement_suggestions(job_desc, resume_text):
    job_kws = extract_top_keywords(job_desc, top_k=20)
    missing_kws = missing_keywords(job_kws, resume_text)
    missing_sections = section_check(resume_text)

    suggestions = []

    if missing_kws:
        suggestions.append({
            "title": "Add missing role-relevant keywords (only if truthful)",
            "details": [
                "These keywords are important in the job description but not found in your resume.",
                "Add them naturally into Skills/Projects/Experience if you genuinely have them.",
                ", ".join(missing_kws[:12]) + (" ..." if len(missing_kws) > 12 else "")
            ]
        })

    if missing_sections:
        suggestions.append({
            "title": "Improve resume structure",
            "details": [
                f"Add or clearly label these sections: {', '.join(missing_sections)}",
                "ATS and recruiters scan headings fast."
            ]
        })

    suggestions.append({
        "title": "Make bullets more measurable",
        "details": [
            "Add numbers: reduced time by X%, improved accuracy by Y%, handled Z requests/day.",
            "Use Action + Tool + Outcome format in bullets."
        ]
    })

    suggestions.append({
        "title": "ATS-friendly formatting tips",
        "details": [
            "Avoid tables/text boxes for important info (ATS may skip them).",
            "Use simple headings, consistent bullet points, and standard fonts."
        ]
    })

    return {
        "top_keywords_from_jd": job_kws[:20],
        "missing_keywords": missing_kws[:25],
        "missing_sections": missing_sections,
        "suggestions": suggestions
    }
