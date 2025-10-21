# service/scorer/train_model.py
"""
Train a simple RandomForestRegressor on synthetic SEO-like data,
save the model as service/scorer/model.joblib.
Run: python service/scorer/train_model.py
"""

import random
from pathlib import Path
import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from .features import extract_features
  # uses your previously created extractor

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "model.joblib"

# small text fragments to synthesize articles quickly
SAMPLE_PARAS = [
    "This article explains the main ideas in simple language.",
    "Learn practical tips and best practices to improve results.",
    "We include clear examples and step-by-step instructions.",
    "This section covers actionable suggestions for readers.",
    "Discover easy ways to apply these ideas in real projects."
]

KEYWORDS_POOL = [
    "seo", "marketing", "content", "rank", "optimization", "blog", "ecommerce",
    "performance", "sitemap", "meta", "title", "backlink"
]

def make_random_article(paragraphs=2):
    paras = []
    for _ in range(paragraphs):
        p = random.choice(SAMPLE_PARAS)
        if random.random() < 0.45:
            p += " " + random.choice(KEYWORDS_POOL)
        paras.append(p)
    return "\n\n".join(paras)

def make_random_page():
    title = " ".join(random.sample(KEYWORDS_POOL, k=random.randint(1,3))).title()
    article = make_random_article(paragraphs=random.randint(1,4))
    keywords = random.sample(KEYWORDS_POOL, k=random.randint(1,4))
    meta = ""
    # mimic minimal analyzer structure expected by extract_features
    page = {"title": title, "article": article, "meta": meta, "keywords": keywords,
            "heading_count": random.randint(0,4),
            "images_count": random.randint(0,3),
            "internal_links": random.randint(0,3),
            "external_links": random.randint(0,3),
            "canonical": random.choice([True, False])}
    return page

def compute_label_from_features(feat: dict) -> float:
    # simple heuristic to create target score (0-100)
    score = 0.0
    score += min(20.0, feat.get("article_words", 0) * 0.05)   # length helps
    score += (10.0 if feat.get("h1_present", 0) else 0.0)
    score += min(30.0, feat.get("readability", 0) * 0.2)       # readability positive
    score += min(20.0, feat.get("title_len", 0) * 0.2)
    score += min(20.0, (feat.get("keyword_density_article", 0) or 0.0) * 100.0)
    return float(max(0.0, min(100.0, score)))

def build_dataset(n_samples=800, seed=42):
    random.seed(seed)
    rows = []
    for _ in range(n_samples):
        page = make_random_page()
        meta = {"domain": "example.com"}
        feat = extract_features(meta, page, keywords=page["keywords"])
        # Add a couple of keys used in label if not present
        feat.setdefault("h1_present", 1 if page.get("heading_count", 0) > 0 else 0)
        feat.setdefault("article_words", feat.get("article_words", 0))
        rows.append((feat, page))
    return rows

def rows_to_matrix(rows):
    # gather feature keys (sorted for consistent ordering)
    keys = sorted({k for feat, _ in rows for k in feat.keys()})
    X = []
    y = []
    for feat, page in rows:
        row = [feat.get(k, 0.0) for k in keys]
        X.append(row)
        y.append(compute_label_from_features(feat))
    return np.array(X), np.array(y), keys

def train_and_save(n_samples=800):
    print("Generating synthetic dataset...")
    rows = build_dataset(n_samples=n_samples)
    X, y, feature_keys = rows_to_matrix(rows)
    print("Dataset shape:", X.shape)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    print("Training model...")
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    print("MAE:", mean_absolute_error(y_test, preds))
    print("R2 :", r2_score(y_test, preds))
    # Save both model and feature key order for later use
    dump({"model": model, "feature_keys": feature_keys}, MODEL_PATH)
    print("Saved model to", MODEL_PATH)

if __name__ == "__main__":
    train_and_save(800)
