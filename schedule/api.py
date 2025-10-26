# schedule/api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

router = APIRouter()

IST = ZoneInfo("Asia/Kolkata")

class ScheduleRequest(BaseModel):
    topic: str = Field(..., description="Topic or campaign theme")
    keywords: List[str] = Field(default_factory=list)
    channel: str = Field("blog", description="blog | linkedin | twitter | instagram | youtube")
    timezone: str = Field("Asia/Kolkata")
    preferred_days: Optional[List[str]] = Field(default=None, description="Optional: ['Mon','Tue',...]")
    history_local_post_hours: Optional[List[int]] = Field(default=None, description="Optional: hours (0-23) that performed well previously")

def _now_tz(tzname: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(tzname))
    except Exception:
        return datetime.now(IST)

# simple channel defaults (local times)
CHANNEL_DEFAULT_SLOTS = {
    "blog":      [10, 14, 20],
    "linkedin":  [9, 12, 18],
    "twitter":   [9, 13, 21],
    "instagram": [11, 16, 19],
    "youtube":   [12, 17, 20],
}

DOW_ORDER = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def _pick_days(preferred: Optional[List[str]]) -> List[str]:
    if preferred:
        vals = [d for d in preferred if d in DOW_ORDER]
        if vals:
            return vals
    # default: weekdays first, then Sat
    return ["Tue","Wed","Thu","Mon","Fri","Sat","Sun"]

def _score_hours(channel: str, history: Optional[List[int]]) -> List[int]:
    base = CHANNEL_DEFAULT_SLOTS.get(channel.lower(), CHANNEL_DEFAULT_SLOTS["blog"])
    if not history:
        return base
    # merge: boost any overlapping historical hours, keep top 3 unique
    boosted = list(dict.fromkeys(history + base))  # keep order, unique
    # clamp to valid 0-23 and return first 3
    boosted = [h for h in boosted if isinstance(h, int) and 0 <= h <= 23]
    return (boosted[:3] or base)

def _next_occurrences(start: datetime, dow_list: List[str], hours: List[int], k: int = 6) -> List[datetime]:
    results: List[datetime] = []
    d = start.replace(minute=0, second=0, microsecond=0)
    # search next ~21 days to collect k slots
    for day_offset in range(0, 22):
        cur = d + timedelta(days=day_offset)
        if DOW_ORDER[cur.weekday()] in dow_list:
            for h in hours:
                slot = cur.replace(hour=h)
                if slot > start:
                    results.append(slot)
                    if len(results) >= k:
                        return results
    return results

@router.post("/suggest", summary="Suggest top posting times for the next 2 weeks")
def suggest_schedule(req: ScheduleRequest) -> Dict[str, Any]:
    now = _now_tz(req.timezone)
    days = _pick_days(req.preferred_days)
    hours = _score_hours(req.channel, req.history_local_post_hours)
    next_slots = _next_occurrences(now, days, hours, k=6)

    rationale = []
    if req.history_local_post_hours:
        rationale.append("Used your past high-engagement hours for ranking.")
    rationale.append(f"Optimized for {req.channel.capitalize()} typical engagement windows.")
    if req.preferred_days:
        rationale.append("Respected your preferred days.")
    else:
        rationale.append("Weighted weekdays (Tue–Thu) which trend higher for B2B.")

    return {
        "topic": req.topic,
        "channel": req.channel,
        "timezone": req.timezone,
        "keywords": req.keywords[:10],
        "recommended_hours_local": hours,
        "recommended_days_order": days,
        "next_slots_local_iso": [dt.isoformat() for dt in next_slots],
        "notes": rationale,
    }
