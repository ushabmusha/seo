"""
FastAPI backend for Smart SEO AI — unified API for:
1. Analyzer
2. Scoring
3. Content Generator (Title, Meta, Article)

This version includes robust OpenAI LLM handling compatible with v1+ SDK.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import requests
import os
from generator.llm_client import generate_from_prompt

# ---------------------- FastAPI Setup ----------------------

app = FastAPI(title="Smart SEO AI API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------- Models ----------------------

class AnalyzeRequest(BaseModel):
    url: str


class ScoreRequest(BaseModel):
    url: str


class GenerateRequest(BaseModel):
    text: str
    kinds: List[str] = ["title", "meta", "article"]
    max_tokens: int = 400
    temperature: float = 0.7


# ---------------------- Utility ----------------------

def _build_prompt_from_features(features: Dict[str, Any], kind: str) -> str:
    """
    Improved prompt templates for better SEO outputs.
    Produces clearer instructions for title / meta / article generation.
    """
    title = features.get("title", "").strip()
    desc = features.get("meta_description", "").strip()
    keywords_list = features.get("top_keywords") or []
    keywords = ", ".join(keywords_list[:8]) if keywords_list else "none"
    domain = features.get("domain", "") or features.get("url", "") or ""
    word_count = features.get("word_count", 0)

    if kind == "title":
        prompt = (
            f"Write 3 concise, click-enticing SEO titles (each <= 70 characters). "
            f"Use the primary keywords: {keywords}. "
            f"Current title: '{title}'. Target audience: general readers. "
            f"Return a JSON array of the 3 titles only."
        )
        return prompt

    if kind == "meta":
        prompt = (
            f"Write 3 SEO meta descriptions (<= 155 characters). "
            f"Include keywords: {keywords}. "
            f"Current meta: '{desc}'. Make them informative, with a subtle CTA. "
            f"Return a JSON array of the 3 meta descriptions only."
        )
        return prompt

    if kind == "article":
        target_words = 700 if word_count < 600 else max(500, int(word_count * 1.2))
        prompt = (
            f"Write an SEO-optimized article (~{target_words} words) for the page. "
            f"Title: '{title}'. Primary keywords: {keywords}. Domain: {domain}. "
            "Structure:\n"
            "- Start with a 2-3 sentence introduction including the main keywords.\n"
            "- Include at least 3 H2 headings with 2–4 short paragraphs under each.\n"
            "- Add 2 bullet lists: one for 'key takeaways', one for 'quick tips'.\n"
            "- End with a short conclusion and call-to-action (CTA).\n"
            "- Use natural tone, short paragraphs, and real-world SEO writing style.\n"
            "Return plain text. Also provide a short 40-word 'summary' and a 3-sentence 'social share blurb'."
        )
        return prompt

    return features.get("text", "")[:800] or "Write an SEO-optimized paragraph."


# ---------------------- ROUTES ----------------------

@app.get("/")
async def root():
    return {"status": "ok", "message": "SEO AI backend ready"}


@app.post("/api/analyze/")
async def analyze_website(req: AnalyzeRequest):
    """Step 1: Extract content from the given URL (mock or real)."""
    url = req.url
    try:
        response = requests.get(url, timeout=10)
        text = response.text[:5000]  # limit for speed
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

    return {
        "url": url,
        "title": "Mock title from extracted webpage",
        "meta_description": "Mock meta description from extracted HTML",
        "word_count": len(text.split()),
        "top_keywords": ["SEO", "content", "optimization", "AI", "marketing"],
    }


@app.post("/api/analyze/score/")
async def analyze_score(req: ScoreRequest):
    """Step 2: Compute SEO score for the analyzed site."""
    url = req.url
    try:
        score = hash(url) % 100  # simple mock score
        return {
            "url": url,
            "overall_score": score,
            "readability_score": 80,
            "keyword_density": 4.5,
            "page_speed_score": 70,
            "recommendation": "Optimize title tags and meta descriptions for better ranking."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {e}")


@app.post("/api/generate/")
async def generate_content(req: GenerateRequest):
    """
    Step 3: Generate new content (title/meta/article) using OpenAI GPT.
    If API key invalid or quota exceeded, uses mock fallback.
    """
    generated_outputs = {}

    for kind in req.kinds:
        try:
            # Build pseudo features for prompt creation
            features = {
                "text": req.text,
                "title": "",
                "meta_description": "",
                "top_keywords": ["SEO", "content", "marketing", "rank"],
                "domain": "example.com",
                "word_count": 800
            }

            prompt = _build_prompt_from_features(features, kind)
            output = generate_from_prompt(prompt, kind=kind, max_tokens=req.max_tokens)
            generated_outputs[kind] = {
                "prompt": prompt,
                "output": output
            }

        except Exception as e:
            generated_outputs[kind] = {"error": str(e)}

    return {"generated": generated_outputs}


# ---------------------- Run Locally ----------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
