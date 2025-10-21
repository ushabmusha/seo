# scorer/scoring.py
from typing import Dict, Any, Tuple, List

def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))

def compute_subscores(features: Dict[str, Any]) -> Tuple[float, float, float, List[str]]:
    """
    Given analyzer features dict, compute:
      - content_score (0-100)
      - technical_score (0-100)
      - onpage_score (0-100)
    Returns (content_score, technical_score, onpage_score, notes[])
    """
    notes = []

    # basic safe reads
    word_count = int(features.get("word_count", 0))
    title = (features.get("title") or "").strip()
    meta = (features.get("meta_description") or "").strip()
    headings = features.get("headings", [])
    images_missing = int(features.get("images_missing_alt", 0))
    links_count = int(features.get("links_count", 0))
    has_schema = bool(features.get("has_schema", False))
    readability = features.get("readability", {}) or {}
    flesch = float(readability.get("flesch", 0.0) or 0.0)

    # --- Content score (quality & length & readability & keywords)
    # word count: ideal 700+ (for long-form), good 300-700, low <300
    wc_score = 0.0
    if word_count >= 1200:
        wc_score = 100
    elif word_count >= 700:
        wc_score = 85
    elif word_count >= 300:
        wc_score = 65
    elif word_count >= 150:
        wc_score = 40
    else:
        wc_score = 10
        notes.append("Very short content — consider adding more helpful content (>300 words).")

    # readability: Flesch reading ease typical range 0-100, higher = easier.
    # bonus for readable content (target 60-80)
    if flesch >= 60:
        read_score = 100
    elif flesch >= 40:
        read_score = 70
    else:
        read_score = 40
        notes.append("Low readability score — consider simplifying sentences and paragraphs.")

    # headings presence (H1/H2)
    h1_count = sum(1 for h in headings if h.get("tag","").lower() == "h1")
    if h1_count == 0:
        notes.append("Missing H1 heading — add a clear H1 with primary keyword.")
    h_score = 100 if h1_count >= 1 else 40

    # content final (weighted)
    content_score = (wc_score * 0.5) + (read_score * 0.3) + (h_score * 0.2)

    # --- Technical score (schema, images, links)
    schema_score = 100 if has_schema else 60
    img_score = 100 if images_missing == 0 else max(20, 100 - images_missing * 10)
    link_score = 100 if links_count >= 3 else (50 if links_count >= 1 else 20)

    if not has_schema:
        notes.append("No structured data (JSON-LD) detected — adding Schema can help rich results.")
    if images_missing > 0:
        notes.append(f"{images_missing} images missing alt text — add alt attributes to images.")

    technical_score = (schema_score * 0.35) + (img_score * 0.35) + (link_score * 0.30)

    # --- On-page score (title/meta length, keyword presence approximated by lengths)
    title_len = len(title)
    meta_len = len(meta)
    title_score = 0
    meta_score = 0

    # title target 50-70 chars, give highest points if within range
    if 40 <= title_len <= 70:
        title_score = 100
    elif title_len > 70:
        title_score = 60
        notes.append("Title is long — consider shortening to 50-70 characters.")
    elif title_len >= 20:
        title_score = 70
    else:
        title_score = 30
        notes.append("Title is short or missing — include target keywords in the title (50-70 chars).")

    # meta target 50-160 chars
    if 50 <= meta_len <= 160:
        meta_score = 100
    elif meta_len > 160:
        meta_score = 60
        notes.append("Meta description is too long — keep it under 160 characters.")
    elif meta_len >= 30:
        meta_score = 70
    else:
        meta_score = 20
        notes.append("Meta description is short or missing — add a clear 50-160 char meta description.")

    onpage_score = (title_score * 0.55) + (meta_score * 0.35) + (h_score * 0.10)

    # clamp and return
    return clamp(content_score), clamp(technical_score), clamp(onpage_score), notes

def compute_overall_score(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry. Returns:
    {
      overall: 0-100,
      breakdown: {content:.., technical:.., onpage:..},
      notes: [...],
      weights: {...}
    }
    """
    content, technical, onpage, notes = compute_subscores(features)

    # Global weights (tunable)
    weights = {"content": 0.5, "technical": 0.25, "onpage": 0.25}

    overall = (content * weights["content"] +
               technical * weights["technical"] +
               onpage * weights["onpage"])

    overall = clamp(overall)

    return {
        "overall_score": round(overall, 2),
        "breakdown": {
            "content": round(content, 2),
            "technical": round(technical, 2),
            "onpage": round(onpage, 2)
        },
        "weights": weights,
        "notes": notes
    }

# quick local test helper (run manually in Python REPL)
if __name__ == "__main__":
    sample = {
        "title": "Best Pancake Recipes",
        "meta_description": "Easy pancake recipes to start your day",
        "headings": [{"tag":"h1","text":"Pancakes"}],
        "images_missing_alt": 1,
        "links_count": 2,
        "has_schema": False,
        "word_count": 250,
        "readability": {"flesch": 65}
    }
    print(compute_overall_score(sample))
