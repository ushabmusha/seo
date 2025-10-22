# competitor/api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

router = APIRouter()

# -------------------- Request Model --------------------
class CompetitorRequest(BaseModel):
    urls: List[str]
    fetch_text: Optional[bool] = False   # if true, include full text (may be large)


# -------------------- Utility Functions --------------------
def _clean_text(s: str) -> str:
    """Remove extra whitespace and newlines."""
    return re.sub(r'\s+', ' ', s).strip()


def _extract_basic_features(html: str, base_url: Optional[str] = None) -> Dict[str, Any]:
    """Extract SEO-relevant features from a competitor page."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    h1 = ""
    h1_tag = soup.find("h1")
    if h1_tag:
        h1 = _clean_text(h1_tag.get_text())

    # Gather headings
    headings = [_clean_text(h.get_text()) for h in soup.find_all(re.compile("^h[1-6]$"))]

    # Word count
    text = _clean_text(soup.get_text(separator=" "))
    word_count = len(re.findall(r"\w+", text))

    # Top keywords (simple frequency-based)
    words = [w.lower() for w in re.findall(r"\w+", text) if len(w) > 3]
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    top_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    top_keywords = [k for k, _ in top_keywords]

    # Image count
    images = len(soup.find_all("img"))

    # Internal / external links
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    internal_links = 0
    external_links = 0
    domain = urlparse(base_url).netloc if base_url else ""
    for href in links:
        try:
            netloc = urlparse(href).netloc
            if netloc == "" or netloc == domain:
                internal_links += 1
            else:
                external_links += 1
        except Exception:
            pass

    return {
        "title": title,
        "meta_description": meta_desc,
        "h1": h1,
        "headings": headings,
        "word_count": word_count,
        "top_keywords": top_keywords,
        "images": images,
        "internal_links": internal_links,
        "external_links": external_links,
        "text_excerpt": text[:2000]  # short excerpt
    }


# -------------------- Routes --------------------
@router.post("/analyze/", summary="Analyze competitor pages (basic metadata)")
def analyze_competitors(req: CompetitorRequest):
    """Fetch and extract SEO features from competitor pages."""
    results = {}
    for url in req.urls:
        try:
            resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0 (seo-agent/1.0)"})
            if resp.status_code != 200:
                results[url] = {"error": f"HTTP {resp.status_code}"}
                continue
            html = resp.text
            features = _extract_basic_features(html, base_url=url)
            if not req.fetch_text:
                features.pop("text_excerpt", None)
            results[url] = {"ok": True, "features": features}
        except requests.RequestException as e:
            results[url] = {"error": str(e)}
        except Exception as e:
            results[url] = {"error": f"extract_failed: {e}"}
    return {"results": results}


@router.post("/compare/", summary="Compare your page against competitors")
def compare_pages(data: Dict[str, Any]):
    """Compare your site's SEO stats with competitors and give recommendations."""
    target = data.get("target", {})
    competitors = data.get("competitors", [])
    if not target or not competitors:
        raise HTTPException(status_code=400, detail="Need both target and competitors data")

    report = []
    metrics = ["word_count", "images", "internal_links", "external_links"]

    for comp in competitors:
        c_title = comp.get("title", "Competitor")
        diff = {}
        for m in metrics:
            diff[m] = target.get(m, 0) - comp.get(m, 0)
        overlap = len(set(target.get("top_keywords", [])) & set(comp.get("top_keywords", [])))
        diff["keyword_overlap"] = overlap
        report.append({
            "competitor": c_title,
            "differences": diff
        })

    # Summary
    avg_words = sum(c.get("word_count", 0) for c in competitors) / len(competitors)
    summary = {
        "target_word_count": target.get("word_count", 0),
        "competitor_avg_words": round(avg_words, 2),
        "recommendation": (
            "Increase content length and keyword coverage"
            if target.get("word_count", 0) < avg_words
            else "Your content length is strong; focus on backlinks and meta tags"
        )
    }

    return {"summary": summary, "detailed": report}

from generator.llm_client import generate_from_prompt  # ✅ reuse your LLM utility

@router.post("/insights/", summary="Generate AI-powered competitor insights")
def competitor_ai_insights(data: Dict[str, Any]):
    """
    Uses GPT to summarize competitive landscape and recommend SEO strategy.
    Input:
      {
        "comparison": { ... result from /competitor/compare/ ... }
      }
    Output:
      AI-generated analysis of strengths, weaknesses, and next steps.
    """
    comparison = data.get("comparison", {})
    if not comparison:
        raise HTTPException(status_code=400, detail="Missing comparison data")

    summary = comparison.get("summary", {})
    detailed = comparison.get("detailed", [])

    prompt = (
        "You are an SEO strategist. Based on this competitor comparison data, "
        "write a concise SEO insight report.\n\n"
        f"Summary: {summary}\n\n"
        f"Details: {detailed}\n\n"
        "Explain:\n"
        "- Overall SEO positioning vs competitors\n"
        "- Strengths of the target site\n"
        "- Weaknesses to improve\n"
        "- 3 prioritized next-step actions for better ranking.\n"
        "Keep the tone professional and under 250 words."
    )

    try:
        ai_response = generate_from_prompt(prompt, kind="insight", max_tokens=350)
        return {"ai_insights": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI insight generation failed: {e}")
