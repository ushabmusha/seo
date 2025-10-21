# service/analyzer/extractor.py
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from typing import Optional

def fetch_html(url: str, timeout: int = 10) -> str:
    """
    Fetch HTML from a URL. Raises requests exceptions on network errors.
    """
    headers = {"User-Agent": "SEO-AI/1.0 (+https://example.com)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def extract_text_from_html(html: str) -> str:
    """
    Remove scripts/styles and return cleaned visible text.
    """
    soup = BeautifulSoup(html, "lxml")
    for s in soup(["script", "style", "noscript"]):
        s.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_meta_and_headings(html: str, base_url: Optional[str] = None) -> dict:
    """
    Extract title, meta description, headings, image alt stats, links count and basic schema presence.
    Returns a dict with keys:
      title, meta_description, headings (list of {tag,text}),
      images_total, images_missing_alt, links_count, has_schema
    """
    soup = BeautifulSoup(html, "lxml")

    # title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # meta description
    meta_desc = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        meta_desc = md.get("content").strip()

    # headings
    headings = []
    for h in soup.find_all(re.compile("^h[1-6]$")):
        headings.append({"tag": h.name, "text": h.get_text(strip=True)})

    # images and alt text
    image_alts = [img.get("alt", "") for img in soup.find_all("img")]
    images_total = len(image_alts)
    images_missing_alt = sum(1 for a in image_alts if not a)

    # links
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if base_url:
            href = urljoin(base_url, href)
        links.append(href)
    links_count = len(links)

    # basic schema detection
    has_schema = bool(soup.find_all("script", type="application/ld+json"))

    return {
        "title": title,
        "meta_description": meta_desc,
        "headings": headings,
        "images_total": images_total,
        "images_missing_alt": images_missing_alt,
        "links_count": links_count,
        "has_schema": has_schema,
    }
