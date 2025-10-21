# service/scorer/api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from .scoring import compute_overall_score

router = APIRouter()

class ScoreRequest(BaseModel):
    """
    Accept the features JSON produced by the analyzer.
    Example: { "title": "...", "meta_description": "...", "word_count": 123, ... }
    """
    features: Optional[Dict[str, Any]] = None

@router.post("/", summary="Compute SEO score from analyzer features")
def score_endpoint(req: ScoreRequest):
    if not req.features:
        raise HTTPException(status_code=400, detail="Provide a 'features' object (analyzer output).")
    try:
        result = compute_overall_score(req.features)
        return {"ok": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring error: {e}")
