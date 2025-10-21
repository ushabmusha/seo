from fastapi import FastAPI
from analyzer.api import router as analyzer_router
from scorer.api import router as scorer_router
from generator import api as generator_module   # ✅ this line stays here

app = FastAPI(title="SEO AI Backend (single-service demo)")  # ✅ this line must come before any app.mount

# Routers
app.include_router(analyzer_router, prefix="/api/analyze", tags=["analyzer"])
app.include_router(scorer_router, prefix="/api/score", tags=["scorer"])

# ✅ Now mount the generator app
app.mount("/api/generate", generator_module.app)

@app.get("/")
def root():
    return {"status": "ok", "message": "SEO AI backend ready"}

