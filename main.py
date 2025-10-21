# main.py
from fastapi import FastAPI
from analyzer.api import router as analyzer_router
from scorer.api import router as scorer_router
from generator.api import router as generator_router   # <-- new

app = FastAPI(title="SEO AI Backend (single-service demo)")

app.include_router(analyzer_router, prefix="/api/analyze", tags=["analyzer"])
app.include_router(scorer_router, prefix="/api/score", tags=["scorer"])
app.include_router(generator_router, prefix="/api/generate", tags=["generator"])  # <-- new

@app.get("/")
def root():
    return {"status": "ok", "message": "SEO AI backend ready"}
