from fastapi import FastAPI
from analyzer.api import router as analyzer_router
from scorer.api import router as scorer_router
from generator import api as generator_module
from competitor.api import router as competitor_router

# ✅ Initialize the FastAPI app
app = FastAPI(title="SEO AI Backend (single-service demo)")

# ✅ Include routers for all modules
app.include_router(analyzer_router, prefix="/api/analyze", tags=["analyzer"])
app.include_router(scorer_router, prefix="/api/score", tags=["scorer"])
app.mount("/api/generate", generator_module.app)
app.include_router(competitor_router, prefix="/competitor", tags=["competitor"])

# ✅ Root endpoint
@app.get("/")
def root():
    return {"status": "ok", "message": "SEO AI backend ready"}



