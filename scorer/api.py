# service/scorer/api.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pathlib import Path
from joblib import load
import numpy as np

router = APIRouter()
MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"

# Use the same feature extractor you created earlier
from .features import extract_features

_loaded = None
_feature_keys = None

def _load_model():
    global _loaded, _feature_keys
    if _loaded is None:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"Model file not found at {MODEL_PATH}. Run scorer/train_model.py first.")
        data = load(MODEL_PATH)
        # Trainer saved a dict {"model": model, "feature_keys": feature_keys} OR joblib may have saved directly
        if isinstance(data, dict) and "model" in data:
            _loaded = data["model"]
            _feature_keys = data.get("feature_keys") or sorted(getattr(data["model"], "feature_names_in_", []) or [])
        else:
            # backward compatibility: treat loaded object as model only
            _loaded = data
            # try to get feature names from estimator if present
            _feature_keys = sorted(getattr(_loaded, "feature_names_in_", [])) if hasattr(_loaded, "feature_names_in_") else None
    return _loaded, _feature_keys

@router.post("/predict/")
def predict_score(payload: Dict[str, Any]):
    """
    Predict an engagement/performance score using the trained model.

    Expected JSON shape:
    {
      "meta": {"domain":"example.com"},
      "page": {
        "title": "...",
        "article": "...",
        "meta": "...",
        "keywords": ["k1","k2"],
        "heading_count": 2,
        "images_count": 1,
        "internal_links": 2,
        "external_links": 0,
        "canonical": true
      }
    }
    """
    try:
        page = payload.get("page", {})
        meta = payload.get("meta", {}) or {}
        keywords = page.get("keywords", [])
        feats = extract_features(meta, page, keywords=keywords)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Feature extraction failed: {e}")

    try:
        model, feature_keys = _load_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Build input vector in the same feature order as training.
    if feature_keys:
        keys = feature_keys
    else:
        # fallback: use sorted keys from feats for consistency
        keys = sorted(feats.keys())

    X = np.array([[feats.get(k, 0.0) for k in keys]])
    try:
        y_pred = model.predict(X)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction failed: {e}")

    return {"score": float(y_pred), "features": feats}
