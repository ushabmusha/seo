# service/scorer/features.py
"""
Simple feature extractor for SEO performance prediction.

Input: dict `analyzer` and dict `generated` (from your analyzer/generator outputs)
Output: dict of numeric features
"""

import math
import re
from textstat import flesch_reading_ease  # pip install textstat

def safe_len(val):
    return 0 if val is None else len(str(val))

def count_words(text):
    if not text:
        return 0
    return len(re.findall(r"\w+", text))

def keyword_density(text, keywords):
    if not text or not keywords:
        return 0.0
    words = re.findall(r"\w+", text.lower())
    total = len(words) or 1
    kcount = sum(words.count(k.lower()) for k in keywords)
    return kcount / total

def avg_sentence_length(text):
    if not text:
        return 0.0
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0.0
    return sum(len(re.findall(r"\w+", s)) for s in sentences) / len(sentences)

def extract_features(analyzer: dict, generated: dict, keywords: list = None):
    """
    analyzer: dict output from service.analyzer (expected keys used below)
    generated: dict output from generator (title, meta, article)
    keywords: list of primary keywords (optional)
    returns: dict of features (floats/ints)
    """
    keywords = keywords or []
    features = {}

    # Basic analyzer-derived features (use safe access)
    features['title_len'] = safe_len(analyzer.get('title', '')) if isinstance(analyzer, dict) else safe_len(generated.get('title',''))
    features['meta_len'] = safe_len(analyzer.get('meta', ''))
    features['h1_present'] = 1 if analyzer.get('h1') else 0
    features['h_count'] = analyzer.get('heading_count', 0) if analyzer.get('heading_count') is not None else 0
    features['images'] = analyzer.get('images_count', 0) if analyzer.get('images_count') is not None else 0
    features['internal_links'] = analyzer.get('internal_links', 0) if analyzer.get('internal_links') is not None else 0
    features['external_links'] = analyzer.get('external_links', 0) if analyzer.get('external_links') is not None else 0
    features['has_canonical'] = 1 if analyzer.get('canonical') else 0

    # Generated content features
    article_text = generated.get('article', '') if isinstance(generated, dict) else ''
    title_text = generated.get('title', '') if isinstance(generated, dict) else ''
    meta_text = generated.get('meta', '') if isinstance(generated, dict) else ''

    features['article_words'] = count_words(article_text)
    features['title_words'] = count_words(title_text)
    features['meta_words'] = count_words(meta_text)
    features['avg_sentence_len'] = avg_sentence_length(article_text)
    try:
        features['readability'] = flesch_reading_ease(article_text) if article_text else 0.0
    except Exception:
        features['readability'] = 0.0

    # keyword metrics
    features['keyword_density_title'] = keyword_density(title_text, keywords)
    features['keyword_density_article'] = keyword_density(article_text, keywords)

    # Derived / ratio features
    features['images_per_100_words'] = (features['images'] / (features['article_words'] or 1)) * 100
    features['links_per_100_words'] = ((features['internal_links'] + features['external_links']) / (features['article_words'] or 1)) * 100

    # Clip/normalize-ish for safety
    # (these keep numeric ranges reasonable for simple models)
    for k, v in list(features.items()):
        if isinstance(v, float) and math.isfinite(v) is False:
            features[k] = 0.0

    return features
