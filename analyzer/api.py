# service/analyzer/api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .extractor import fetch_html, extract_text_from_html, extract_meta_and_headings
from .features import top_keywords_from_text, readability_scores

router = APIRouter()

class AnalyzeRequest(BaseModel):
    url: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None

@router.post("/", summary="Analyze HTML or URL and return SEO features")
def analyze(req: AnalyzeRequest):
    """
    POST /api/analyze/ 
    Body: { "url": "...", "html": "...", "text": "..." }
    Prefers url -> html -> text in that order.
    """
    html = None
    if req.url:
        try:
            html = fetch_html(req.url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")
    elif req.html:
        html = req.html
    elif req.text:
        html = f"<html><body><p>{req.text}</p></body></html>"
    else:
        raise HTTPException(status_code=400, detail="Provide url or html or text")

    # Extract meta/headings & cleaned text
    meta = extract_meta_and_headings(html, base_url=req.url)
    text = extract_text_from_html(html)

    # Compute features
    keywords = top_keywords_from_text(text, max_keywords=12)
    read_scores = readability_scores(text)

    # Rules-based recommendations (simple)
    recs = []
    if len(meta.get("meta_description", "")) < 50:
        recs.append("Meta description is too short (recommended 50-160 chars)")
    if len(meta.get("title", "")) < 30:
        recs.append("Title looks short (consider 50-70 chars with target keywords)")
    if read_scores.get("word_count", 0) < 200:
        recs.append("Content is short — consider adding more helpful content (>300 words recommended)")
    if meta.get("images_missing_alt", 0) > 0:
        recs.append(f"{meta['images_missing_alt']} images missing alt text")

    result = {
        "title": meta.get("title", ""),
        "meta_description": meta.get("meta_description", ""),
        "headings": meta.get("headings", []),
        "images_total": meta.get("images_total", 0),
        "images_missing_alt": meta.get("images_missing_alt", 0),
        "links_count": meta.get("links_count", 0),
        "has_schema": meta.get("has_schema", False),
        "word_count": read_scores.get("word_count", 0),
        "sentence_count": read_scores.get("sentence_count", 0),
        "readability": {
            "flesch": read_scores.get("flesch_reading_ease"),
            "fk_grade": read_scores.get("flesch_kincaid_grade")
        },
        "top_keywords": keywords,
        "recommendations": recs
    }

    return result
# ---- paste below existing code in service/analyzer/api.py ----
from scorer.scoring import compute_overall_score

@router.post("/score/", summary="Analyze input and return features + score")
def analyze_and_score(req: AnalyzeRequest):
    """
    Combined endpoint:
     - runs the analyzer (same logic as /)
     - then runs the scorer on the analyzer output
     - returns both features and scoring result
    """
    # Reuse existing analyze logic by duplicating minimal parts here
    html = None
    if req.url:
        try:
            html = fetch_html(req.url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")
    elif req.html:
        html = req.html
    elif req.text:
        html = f"<html><body><p>{req.text}</p></body></html>"
    else:
        raise HTTPException(status_code=400, detail="Provide url or html or text")

    meta = extract_meta_and_headings(html, base_url=req.url)
    text = extract_text_from_html(html)

    keywords = top_keywords_from_text(text, max_keywords=12)
    read_scores = readability_scores(text)

    # Build analyzer features dict (same structure returned by /)
    features = {
        "title": meta.get("title", ""),
        "meta_description": meta.get("meta_description", ""),
        "headings": meta.get("headings", []),
        "images_total": meta.get("images_total", 0),
        "images_missing_alt": meta.get("images_missing_alt", 0),
        "links_count": meta.get("links_count", 0),
        "has_schema": meta.get("has_schema", False),
        "word_count": read_scores.get("word_count", 0),
        "sentence_count": read_scores.get("sentence_count", 0),
        "readability": {
            "flesch": read_scores.get("flesch_reading_ease"),
            "fk_grade": read_scores.get("flesch_kincaid_grade"),
        },
        "top_keywords": keywords
    }

    # simple recommendations (reuse rules)
    recs = []
    if len(features["meta_description"]) < 50:
        recs.append("Meta description is too short (recommended 50-160 chars)")
    if len(features["title"]) < 30:
        recs.append("Title looks short (consider 50-70 chars with target keywords)")
    if features.get("word_count", 0) < 200:
        recs.append("Content is short — consider adding more helpful content (>300 words recommended)")
    if features.get("images_missing_alt", 0) > 0:
        recs.append(f"{features['images_missing_alt']} images missing alt text")

    features["recommendations"] = recs

    # compute score using scorer
    try:
        score_result = compute_overall_score(features)
    except Exception as e:
        # If scoring fails, still return features and an error note
        score_result = {"error": f"Scoring failed: {e}"}

    return {
        "features": features,
        "score": score_result
    }
# ---- end paste ----
