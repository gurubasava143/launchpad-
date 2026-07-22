# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Query, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import List, Optional
import os

import db
import aggregator

app = FastAPI(
    title="IT Job Aggregator for Freshers",
    description="A centralized job aggregator API focusing on entry-level (0-2 years) IT roles.",
    version="1.0.0"
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup hook to initialize the database
@app.on_event("startup")
def startup_event():
    db.init_db()

@app.get("/api/jobs")
def get_jobs(
    search: Optional[str] = None,
    experience: Optional[str] = None, # Comma-separated: "0,0-1,0-2"
    skills: Optional[str] = None, # Comma-separated: "Python,React"
    locations: Optional[str] = None, # Comma-separated: "Remote,Bengaluru"
    company_types: Optional[str] = None, # Comma-separated: "Startup,MNC"
    posted_within: Optional[str] = None, # "24h", "week", "month"
    bookmarks_only: bool = False
):
    """
    Returns lists of primary jobs satisfying the query filters,
    including linked duplicate jobs inside each primary job.
    """
    try:
        # Parse comma-separated filter arguments
        exp_list = [e.strip() for e in experience.split(",")] if experience else None
        skills_list = [s.strip() for s in skills.split(",")] if skills else None
        loc_list = [l.strip() for l in locations.split(",")] if locations else None
        comp_list = [c.strip() for c in company_types.split(",")] if company_types else None
        
        jobs = db.get_filtered_jobs(
            search_query=search,
            experience_levels=exp_list,
            skills=skills_list,
            locations=loc_list,
            company_types=comp_list,
            posted_within=posted_within,
            bookmarks_only=bookmarks_only
        )
        return {"status": "success", "count": len(jobs), "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

@app.post("/api/jobs/sync")
def sync_jobs():
    """Triggers the scraper and deduplication engine."""
    try:
        result = aggregator.sync_all_jobs()
        stats = db.get_stats()
        return {
            "status": "success",
            "message": "Aggregation and deduplication complete.",
            "synced_count": result["total_fetched"],
            "duplicates_detected": result["duplicates_detected"],
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@app.post("/api/jobs/{job_id}/bookmark")
def toggle_job_bookmark(job_id: str):
    """Toggles bookmark status for a specific job."""
    try:
        is_bookmarked = db.toggle_bookmark(job_id)
        return {
            "status": "success",
            "job_id": job_id,
            "is_bookmarked": is_bookmarked,
            "message": "Bookmark added" if is_bookmarked else "Bookmark removed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle bookmark: {str(e)}")

@app.get("/api/stats")
def get_dashboard_stats():
    """Retrieves high-level analytics for the dashboard cards and charts."""
    try:
        stats = db.get_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")

# Ensure static directory exists
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)

# Mount the static files router to serve index.html, index.css and index.js
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
