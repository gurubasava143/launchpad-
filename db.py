import sqlite3
import json
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            experience_level TEXT NOT NULL, -- '0', '0-1', '0-2'
            salary TEXT,
            skills TEXT, -- JSON array of strings
            posted_date TEXT NOT NULL, -- YYYY-MM-DD
            source TEXT NOT NULL, -- Naukri, Indeed, LinkedIn, etc.
            url TEXT NOT NULL,
            is_duplicate INTEGER DEFAULT 0, -- 0 or 1
            duplicate_of_id TEXT,
            company_type TEXT, -- MNC, Startup, etc.
            created_at TEXT NOT NULL,
            FOREIGN KEY (duplicate_of_id) REFERENCES jobs(id)
        )
    """)
    
    # Create bookmarks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            job_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def save_job(job):
    """
    Saves or updates a job.
    job: dict containing title, company, location, experience_level, salary, skills (list), posted_date, source, url, is_duplicate, duplicate_of_id, company_type
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    job_id = job['id']
    skills_json = json.dumps(job.get('skills', []))
    created_at = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT OR REPLACE INTO jobs (
            id, title, company, location, experience_level, salary, skills, posted_date, source, url, is_duplicate, duplicate_of_id, company_type, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id,
        job['title'],
        job['company'],
        job['location'],
        job['experience_level'],
        job.get('salary', 'Not Disclosed'),
        skills_json,
        job['posted_date'],
        job['source'],
        job['url'],
        1 if job.get('is_duplicate', False) else 0,
        job.get('duplicate_of_id'),
        job.get('company_type', 'Startup'),
        created_at
    ))
    
    conn.commit()
    conn.close()

def get_filtered_jobs(
    search_query=None,
    experience_levels=None,
    skills=None,
    locations=None,
    company_types=None,
    posted_within=None,
    bookmarks_only=False
):
    """
    Fetches jobs matching filter criteria. Returns only non-duplicate jobs as top level,
    attaching a list of duplicates (alternative sources) to each job object.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Base query for active jobs (exclude duplicates initially, we will join/query them later)
    # If bookmarks_only is true, we filter by what's in the bookmarks table
    query = """
        SELECT j.*, (b.job_id IS NOT NULL) as is_bookmarked
        FROM jobs j
        LEFT JOIN bookmarks b ON j.id = b.job_id
        WHERE j.is_duplicate = 0
    """
    params = []
    
    # 1. Bookmarks filter
    if bookmarks_only:
        query = """
            SELECT j.*, 1 as is_bookmarked
            FROM jobs j
            INNER JOIN bookmarks b ON j.id = b.job_id
            WHERE 1=1 -- duplicates might be bookmarked, but normally they aren't shown at top
        """
    
    # 2. Search keyword
    if search_query:
        query += " AND (j.title LIKE ? OR j.company LIKE ? OR j.location LIKE ? OR j.skills LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term, term])
        
    # 3. Experience level filter (e.g. ['0', '0-1', '0-2'])
    if experience_levels:
        placeholders = ",".join(["?"] * len(experience_levels))
        query += f" AND j.experience_level IN ({placeholders})"
        params.extend(experience_levels)
        
    # 4. Locations filter
    if locations:
        location_clauses = []
        for loc in locations:
            if loc.lower() == 'remote':
                location_clauses.append("j.location LIKE '%Remote%'")
            else:
                location_clauses.append("j.location LIKE ?")
                params.append(f"%{loc}%")
        query += f" AND ({' OR '.join(location_clauses)})"
        
    # 5. Company type filter
    if company_types:
        placeholders = ",".join(["?"] * len(company_types))
        query += f" AND j.company_type IN ({placeholders})"
        params.extend(company_types)
        
    # 6. Skills filter (Checking JSON tags)
    if skills:
        skill_clauses = []
        for skill in skills:
            skill_clauses.append("j.skills LIKE ?")
            params.append(f"%{skill}%")
        query += f" AND ({' OR '.join(skill_clauses)})"
        
    # 7. Date posted filter (24h, week, month)
    if posted_within:
        today = datetime.now()
        if posted_within == '24h':
            date_limit = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        elif posted_within == 'week':
            date_limit = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        elif posted_within == 'month':
            date_limit = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        else:
            date_limit = None
            
        if date_limit:
            query += " AND j.posted_date >= ?"
            params.append(date_limit)
            
    # Sort by posted date descending
    query += " ORDER BY j.posted_date DESC, j.created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Process output and fetch duplicates for each job
    jobs = []
    for r in rows:
        job = dict(r)
        job['skills'] = json.loads(job['skills']) if job['skills'] else []
        job['is_bookmarked'] = bool(job['is_bookmarked'])
        job['is_duplicate'] = bool(job['is_duplicate'])
        
        # Query for duplicates of this job
        cursor.execute("""
            SELECT id, source, url, salary, posted_date 
            FROM jobs 
            WHERE duplicate_of_id = ?
        """, (job['id'],))
        duplicates = [dict(d) for d in cursor.fetchall()]
        job['duplicates'] = duplicates
        
        jobs.append(job)
        
    conn.close()
    return jobs

def toggle_bookmark(job_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if bookmarked
    cursor.execute("SELECT 1 FROM bookmarks WHERE job_id = ?", (job_id,))
    exists = cursor.fetchone()
    
    is_bookmarked = False
    if exists:
        cursor.execute("DELETE FROM bookmarks WHERE job_id = ?", (job_id,))
    else:
        cursor.execute("INSERT INTO bookmarks (job_id, created_at) VALUES (?, ?)", (job_id, datetime.now().isoformat()))
        is_bookmarked = True
        
    conn.commit()
    conn.close()
    return is_bookmarked

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total jobs (excluding duplicates)
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE is_duplicate = 0")
    total_active_jobs = cursor.fetchone()[0]
    
    # Total duplicates detected
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE is_duplicate = 1")
    total_duplicates = cursor.fetchone()[0]
    
    # New today count (posted in last 24h)
    today_str = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE posted_date >= ? AND is_duplicate = 0", (today_str,))
    new_today = cursor.fetchone()[0]
    
    # Bookmarked count
    cursor.execute("SELECT COUNT(*) FROM bookmarks")
    bookmarked = cursor.fetchone()[0]
    
    # Jobs by source
    cursor.execute("SELECT source, COUNT(*) as count FROM jobs GROUP BY source")
    by_source = {row['source']: row['count'] for row in cursor.fetchall()}
    
    # Top 5 locations
    cursor.execute("SELECT location, COUNT(*) as count FROM jobs WHERE is_duplicate = 0 GROUP BY location ORDER BY count DESC LIMIT 5")
    top_locations = [{row['location']: row['count']} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_active_jobs": total_active_jobs,
        "total_duplicates": total_duplicates,
        "new_today": new_today,
        "bookmarked": bookmarked,
        "by_source": by_source,
        "top_locations": top_locations
    }

def clear_all_jobs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookmarks")
    cursor.execute("DELETE FROM jobs")
    conn.commit()
    conn.close()
