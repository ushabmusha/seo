# main.py
from fastapi import FastAPI
from analyzer.api import router as analyzer_router
from scorer.api import router as scorer_router
from generator import api as generator_module
from competitor.api import router as competitor_router

# ✅ NEW: scheduler + monitor utilities
from apscheduler.schedulers.background import BackgroundScheduler
from monitor.jobs import monitor_once, set_watch_urls, get_watch_urls

app = FastAPI(title="SEO AI Backend (single-service demo)")

# Routers
app.include_router(analyzer_router, prefix="/api/analyze", tags=["analyzer"])
app.include_router(scorer_router, prefix="/api/score", tags=["scorer"])
app.mount("/api/generate", generator_module.app)
app.include_router(competitor_router, prefix="/competitor", tags=["competitor"])

# ---- Monitoring scheduler ----
scheduler = BackgroundScheduler(timezone="UTC")

@app.on_event("startup")
def _start_scheduler():
    # every 30 minutes — adjust if needed
    if not scheduler.get_jobs():
        scheduler.add_job(monitor_once, "interval", minutes=30, id="seo-monitor")
    scheduler.start()

@app.on_event("shutdown")
def _shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)

# ---- Monitor endpoints ----
@app.post("/monitor/run-now", tags=["monitor"])
def monitor_run_now():
    """Run one monitoring cycle immediately."""
    return monitor_once()

@app.get("/monitor/config", tags=["monitor"])
def monitor_get_config():
    """Return current list of watched URLs."""
    return {"urls": get_watch_urls()}

@app.post("/monitor/config", tags=["monitor"])
def monitor_set_config(payload: dict):
    """Set list of watched URLs. Payload: {"urls": ["https://...","https://..."]}"""
    urls = payload.get("urls", [])
    saved = set_watch_urls(urls)
    return {"saved_urls": saved, "count": len(saved)}

# Root
@app.get("/")
def root():
    return {"status": "ok", "message": "SEO AI backend ready"}
