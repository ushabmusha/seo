# monitor/jobs.py
"""
Monitoring jobs: supports configurable watch URLs via a small JSON file.
Endpoints will call set_watch_urls()/get_watch_urls(); monitor_once() reads them.
"""

import os, json, time, requests

BASE_URL = os.getenv("SEO_API_BASE", "http://127.0.0.1:8001")
DATA_DIR = os.path.join(os.path.dirname(__file__))
URLS_PATH = os.path.join(DATA_DIR, "urls.json")

DEFAULT_URLS = ["https://example.com"]

def _load_urls():
    try:
        if os.path.exists(URLS_PATH):
            with open(URLS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data
        return DEFAULT_URLS
    except Exception:
        return DEFAULT_URLS

def _save_urls(urls):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(URLS_PATH, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=2)

def set_watch_urls(urls):
    """Set the list of URLs to watch (and persist to monitor/urls.json)."""
    cleaned = [u for u in urls if isinstance(u, str) and u.strip()]
    if not cleaned:
        cleaned = DEFAULT_URLS
    _save_urls(cleaned)
    return cleaned

def get_watch_urls():
    """Return current list of URLs to watch."""
    return _load_urls()

def monitor_once():
    """Run one monitoring cycle over current watch URLs."""
    watch_urls = _load_urls()
    results = {}
    for url in watch_urls:
        try:
            # 1) Analyze
            r = requests.post(f"{BASE_URL}/api/analyze/", json={"url": url}, timeout=15)
            r.raise_for_status()
            ana = r.json()

            # 2) Score (quick payload)
            page = {
                "title": ana.get("title") or "",
                "article": (ana.get("title") or "") + " " + (ana.get("meta_description") or ""),
                "meta": ana.get("meta_description") or "",
                "keywords": ana.get("top_keywords") or [],
                "heading_count": 1,
                "images_count": 0,
                "internal_links": 0,
                "external_links": 0,
                "canonical": True,
            }
            r2 = requests.post(f"{BASE_URL}/api/score/predict/", json={"meta": {"domain": "monitor.local"}, "page": page}, timeout=15)
            r2.raise_for_status()
            score = r2.json()

            results[url] = {"analyze": ana, "score": score.get("score")}
        except Exception as e:
            results[url] = {"error": str(e)}

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[monitor] {ts} summary:\n{json.dumps(results, indent=2)}")
    return results
