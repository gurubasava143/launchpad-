import requests
import json
import random
import hashlib
import difflib
from datetime import datetime, timedelta
import db

# Optional Adzuna API credentials. Can be set via environment variables.
ADZUNA_APP_ID = "d5d9c228"  # A demo/placeholder key
ADZUNA_APP_KEY = "c8942b03fb4ff99912093e0b200b3d88" # A demo/placeholder key

def generate_job_id(title, company, location, source):
    """Generates a stable unique ID based on core fields to prevent database pollution."""
    payload = f"{title.lower().strip()}|{company.lower().strip()}|{location.lower().strip()}|{source.lower().strip()}"
    return hashlib.md5(payload.encode('utf-8')).hexdigest()

def normalize_company(name):
    """Normalizes company names to handle things like 'TCS' vs 'Tata Consultancy Services'."""
    name = name.lower().strip()
    # Remove common corporate suffixes
    suffixes = [
        "pvt ltd", "private limited", "ltd", "limited", "inc.", "inc", 
        "technologies", "tech", "solutions", "services", "co.", "corporation", "corp"
    ]
    for s in suffixes:
        if name.endswith(" " + s):
            name = name[:-len(s)-1].strip()
        elif name.endswith(s):
            name = name[:-len(s)].strip()
            
    # Manual aliases
    aliases = {
        "tcs": "tata consultancy services",
        "tata consultancy": "tata consultancy services",
        "wipro": "wipro",
        "infosys": "infosys",
        "cognizant": "cognizant",
        "accenture": "accenture",
        "capgemini": "capgemini",
        "hcl": "hcl tech",
        "hcltech": "hcl tech",
        "l&t": "larsen & toubro",
        "larsen and toubro": "larsen & toubro",
    }
    return aliases.get(name, name)

def normalize_location(loc):
    """Maps common city spelling variations to standard names."""
    loc = loc.lower().strip()
    mappings = {
        "bangalore": "bengaluru",
        "bengaluru": "bengaluru",
        "gurgaon": "gurugram",
        "gurugram": "gurugram",
        "bombay": "mumbai",
        "mumbai": "mumbai",
        "calcutta": "kolkata",
        "kolkata": "kolkata",
        "madras": "chennai",
        "chennai": "chennai",
        "delhi/ncr": "delhi ncr",
        "delhi ncr": "delhi ncr",
        "new delhi": "delhi ncr",
        "delhi": "delhi ncr",
        "remote": "remote",
        "wfh": "remote",
        "work from home": "remote"
    }
    for key, val in mappings.items():
        if key in loc:
            return val
    return loc

def clean_title(title):
    t = title.lower()
    # Replace characters
    for char in ["(", ")", "-", "/", "[", "]", ",", "&"]:
        t = t.replace(char, " ")
    
    # Normalize common abbreviations
    replacements = {
        "quality assurance": "qa",
        "react js": "react",
        "reactjs": "react",
        "node js": "node",
        "nodejs": "node",
        "javascript": "js",
        "fresher": "",
        "internship": "intern",
        "entry level": "",
        "associate": "",
        "junior": "",
        "jr": "",
        "sr": "",
        "senior": "",
        "engineer": "developer"
    }
    for old, new in replacements.items():
        t = t.replace(old, new)
        
    # Return unique words sorted to allow order-independent comparisons
    words = [w for w in t.split() if w not in ["developer", "role", "position", "trainee", "jobs"]]
    return sorted(list(set(words)))

def is_duplicate_job(job1, job2):
    """
    Returns True if job1 and job2 are fuzzy duplicates.
    Checks:
    1. Locations match (both remote, or similar city names)
    2. Companies match (similarity > 0.82 or containment after normalization)
    3. Job titles match (Jaccard similarity index >= 0.5 of cleaned keywords)
    """
    # Check location match
    loc1 = normalize_location(job1['location'])
    loc2 = normalize_location(job2['location'])
    if loc1 != loc2:
        return False
        
    # Check company match
    comp1 = normalize_company(job1['company'])
    comp2 = normalize_company(job2['company'])
    comp_ratio = difflib.SequenceMatcher(None, comp1, comp2).ratio()
    
    comp_match = (comp1 == comp2) or (comp1 in comp2) or (comp2 in comp1) or (comp_ratio > 0.82)
    if not comp_match:
        return False
        
    # Check title match (Jaccard Similarity)
    words1 = clean_title(job1['title'])
    words2 = clean_title(job2['title'])
    
    if not words1 or not words2:
        return False
        
    set1 = set(words1)
    set2 = set(words2)
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    jaccard = len(intersection) / len(union) if union else 0
    
    return jaccard >= 0.5

def run_deduplication():
    """
    Scans the database for potential duplicate jobs.
    Runs an O(N^2) pairwise comparison of non-duplicate jobs.
    Flags older/duplicate postings and marks them as duplicate of the primary posting.
    """
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    # Reset duplication flags before running deduplication
    cursor.execute("UPDATE jobs SET is_duplicate = 0, duplicate_of_id = NULL")
    conn.commit()
    
    # Load all jobs sorted by posted date DESC, so we keep the newest or primary one
    cursor.execute("SELECT * FROM jobs ORDER BY posted_date DESC, created_at DESC")
    all_jobs = [dict(row) for row in cursor.fetchall()]
    
    duplicates_to_update = []
    
    # Compare each job with every other job
    for i in range(len(all_jobs)):
        job1 = all_jobs[i]
        
        # If job1 was already flagged as a duplicate of some other job, skip it
        if job1['id'] in [d[0] for d in duplicates_to_update]:
            continue
            
        for j in range(i + 1, len(all_jobs)):
            job2 = all_jobs[j]
            
            # Skip if job2 is already flagged
            if job2['id'] in [d[0] for d in duplicates_to_update]:
                continue
                
            # If they are duplicates, flag job2 as duplicate of job1
            if is_duplicate_job(job1, job2):
                duplicates_to_update.append((job2['id'], job1['id']))
                
    # Update duplicates in database
    for dup_id, primary_id in duplicates_to_update:
        cursor.execute(
            "UPDATE jobs SET is_duplicate = 1, duplicate_of_id = ? WHERE id = ?",
            (primary_id, dup_id)
        )
        
    conn.commit()
    conn.close()
    return len(duplicates_to_update)

def fetch_adzuna_jobs():
    """Fetches real jobs from Adzuna API in India."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("Adzuna API keys not provided. Skipping...")
        return []
        
    jobs = []
    # Search for developer jobs in India
    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 20,
        "what": "software developer junior",
        "content-type": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            for r in results:
                title = r.get("title", "")
                company = r.get("company", {}).get("display_name", "Confidential")
                location = r.get("location", {}).get("display_name", "India")
                salary_min = r.get("salary_min")
                salary_max = r.get("salary_max")
                
                # Check if it sounds like a senior/manager role (sometimes happens in API)
                exclude_terms = ["senior", "sr.", "lead", "manager", "architect", "head"]
                if any(term in title.lower() for term in exclude_terms):
                    continue
                    
                # Format salary
                salary = "Not Disclosed"
                if salary_min and salary_max:
                    salary = f"₹{int(salary_min):,}/yr - ₹{int(salary_max):,}/yr"
                elif salary_min:
                    salary = f"₹{int(salary_min):,}/yr"
                
                # Parse posted date
                created = r.get("created", "") # e.g. "2026-07-20T12:00:00Z"
                try:
                    posted_date = datetime.strptime(created[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
                except:
                    posted_date = datetime.now().strftime("%Y-%m-%d")
                
                # Extract some tags from description/title
                description = r.get("description", "").lower()
                all_skills = ["python", "java", "react", "javascript", "node", "django", "html", "css", "qa", "testing", "sql", "angular"]
                skills = [skill.capitalize() for skill in all_skills if skill in description or skill in title.lower()]
                if not skills:
                    skills = ["Software Development"]
                    
                # Experience deduction
                exp = "0-1 yrs"
                if "intern" in title.lower() or "internship" in description:
                    exp = "0 yrs"
                elif "2 years" in description or "2 yrs" in description:
                    exp = "0-2 yrs"
                    
                # Company type
                company_type = "MNC" if random.random() > 0.5 else "Product-based"
                
                # Apply url
                redirect_url = r.get("redirect_url", "")
                
                job_id = generate_job_id(title, company, location, "Adzuna")
                
                jobs.append({
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "experience_level": exp,
                    "salary": salary,
                    "skills": skills,
                    "posted_date": posted_date,
                    "source": "Adzuna",
                    "url": redirect_url,
                    "company_type": company_type
                })
        else:
            print(f"Adzuna API returned status {response.status_code}")
    except Exception as e:
        print(f"Failed to fetch Adzuna jobs: {e}")
        
    return jobs

def generate_mock_jobs():
    """Generates detailed developer, QA, and web designer jobs to simulate scrapers with duplicates."""
    titles = [
        "Junior Python Developer", "Full Stack Web Developer (MERN)", "Java Developer Intern",
        "React JS Engineer", "QA Automation Analyst", "Django Backend Intern",
        "Associate Software Engineer", "Frontend Developer", "Python/Django Software Engineer",
        "Data Analyst Intern", "Graduate Engineer Trainee", "Support Engineer"
    ]
    
    companies = [
        "Tata Consultancy Services", "Infosys", "Wipro Technologies", "Zomato",
        "Razorpay", "Swiggy", "Cred", "Paytm", "Flipkart", "Ola Cabs",
        "Zepto", "Groww", "InMobi", "Freshworks", "Zoho Corporation",
        "PhonePe", "Meesho", "Nykaa", "Cognizant", "Accenture India"
    ]
    
    locations = [
        "Bengaluru, Karnataka", "Remote", "Pune, Maharashtra", "Gurugram, Haryana",
        "Mumbai, Maharashtra", "Hyderabad, Telangana", "Chennai, Tamil Nadu", "Delhi NCR"
    ]
    
    skills_map = {
        "Python": ["Python", "Django", "SQL", "Git"],
        "Full Stack": ["JavaScript", "React", "Node.js", "Express", "MongoDB"],
        "Java": ["Java", "Spring Boot", "MySQL", "Hibernate"],
        "React": ["React", "JavaScript", "HTML", "CSS", "Tailwind"],
        "QA": ["Selenium", "Python", "Manual Testing", "QA", "Jira"],
        "Django": ["Python", "Django", "REST API", "PostgreSQL"],
        "Associate": ["Java", "Python", "SQL", "C++", "OOD"],
        "Frontend": ["HTML", "CSS", "JavaScript", "React", "Sass"],
        "Data Analyst": ["Python", "Excel", "SQL", "Pandas", "Tableau"],
        "Graduate": ["C++", "Java", "Database Concepts", "Communication Skills"],
        "Support": ["Linux", "SQL", "Troubleshooting", "Networking"]
    }
    
    salaries = [
        "₹3,50,000 - ₹5,00,000 / yr", "₹4,00,000 / yr", "₹6,00,000 - ₹8,00,000 / yr",
        "₹15,000 - ₹25,000 / month", "₹3,00,000 / yr", "₹12,00,000 / yr", "Not Disclosed"
    ]
    
    sources = ["LinkedIn Jobs", "Naukri.com", "Indeed India", "Internshala", "Wellfound", "Foundit"]
    company_types = ["MNC", "Startup", "Service-based", "Product-based"]
    
    jobs = []
    today = datetime.now()
    
    # 1. Generate base mock jobs (distinct ones)
    for i in range(35):
        title = random.choice(titles)
        company = random.choice(companies)
        location = random.choice(locations)
        source = random.choice(sources)
        
        # Determine skills
        core_key = "Associate"
        for key in skills_map.keys():
            if key.lower() in title.lower():
                core_key = key
                break
        skills = skills_map[core_key]
        
        # Experience level based on title
        if "intern" in title.lower():
            exp = "0 yrs"
            salary = random.choice(["₹15,000 - ₹25,000 / month", "₹10,000 / month", "₹30,000 / month"])
            comp_type = "Startup" if random.random() > 0.3 else "Product-based"
        else:
            exp = random.choice(["0-1 yrs", "0-2 yrs"])
            salary = random.choice(salaries)
            comp_type = random.choice(company_types)
            
        # Date posted: within last 15 days
        days_ago = random.randint(0, 15)
        posted_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        # Apply url
        url_company = company.lower().replace(" ", "")
        url_title = title.lower().replace(" ", "-")
        url = f"https://www.{source.split()[0].lower()}.com/jobs/{url_company}-{url_title}-{random.randint(100000, 999999)}"
        
        job_id = generate_job_id(title, company, location, source)
        
        jobs.append({
            "id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "experience_level": exp,
            "salary": salary,
            "skills": skills,
            "posted_date": posted_date,
            "source": source,
            "url": url,
            "company_type": comp_type
        })
        
    # 2. INTENTIONALLY GENERATE DUPLICATES to demonstrate deduplication engine
    # Duplicate pair 1: Python Developer at TCS (Naukri vs LinkedIn)
    date1 = (today - timedelta(hours=6)).strftime("%Y-%m-%d")
    date2 = (today - timedelta(hours=12)).strftime("%Y-%m-%d")
    
    jobs.append({
        "id": generate_job_id("Junior Python Developer", "Tata Consultancy Services", "Bengaluru, Karnataka", "Naukri.com"),
        "title": "Junior Python Developer",
        "company": "Tata Consultancy Services",
        "location": "Bengaluru, Karnataka",
        "experience_level": "0-1 yrs",
        "salary": "₹3,50,000 - ₹4,50,000 / yr",
        "skills": ["Python", "Django", "SQL"],
        "posted_date": date1,
        "source": "Naukri.com",
        "url": "https://www.naukri.com/job/tcs-python-fresher-1234",
        "company_type": "MNC"
    })
    jobs.append({
        "id": generate_job_id("Python Developer - Fresher", "TCS", "Bangalore", "LinkedIn Jobs"),
        "title": "Python Developer - Fresher",
        "company": "TCS",
        "location": "Bangalore",
        "experience_level": "0-1 yrs",
        "salary": "Not Disclosed",
        "skills": ["Python", "Django", "SQL", "Git"],
        "posted_date": date2,
        "source": "LinkedIn Jobs",
        "url": "https://www.linkedin.com/jobs/view/tcs-python-dev-9876",
        "company_type": "MNC"
    })

    # Duplicate pair 2: React JS Engineer at Swiggy (Indeed vs Wellfound)
    date3 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    jobs.append({
        "id": generate_job_id("React JS Engineer", "Swiggy", "Remote", "Indeed India"),
        "title": "React JS Engineer",
        "company": "Swiggy",
        "location": "Remote",
        "experience_level": "0-2 yrs",
        "salary": "₹8,00,000 - ₹12,00,000 / yr",
        "skills": ["React", "JavaScript", "HTML", "CSS"],
        "posted_date": date3,
        "source": "Indeed India",
        "url": "https://www.indeed.co.in/viewjob?jk=swiggy-react-0011",
        "company_type": "Product-based"
    })
    jobs.append({
        "id": generate_job_id("Frontend Engineer (React)", "Swiggy", "Work From Home", "Wellfound"),
        "title": "Frontend Engineer (React)",
        "company": "Swiggy Ltd.",
        "location": "Work From Home",
        "experience_level": "0-2 yrs",
        "salary": "₹9,00,000 - ₹11,00,000 / yr",
        "skills": ["React", "JavaScript", "Redux"],
        "posted_date": date3,
        "source": "Wellfound",
        "url": "https://www.wellfound.com/jobs/swiggy-frontend-engineer-react",
        "company_type": "Product-based"
    })

    # Duplicate pair 3: QA Intern at Swiggy (LinkedIn vs Internshala)
    date4 = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    jobs.append({
        "id": generate_job_id("QA Automation Analyst Intern", "Swiggy", "Bengaluru, Karnataka", "LinkedIn Jobs"),
        "title": "QA Automation Analyst Intern",
        "company": "Swiggy",
        "location": "Bengaluru, Karnataka",
        "experience_level": "0 yrs",
        "salary": "₹20,00,000 / yr",  # Typo in LinkedIn!
        "skills": ["Selenium", "Python", "QA"],
        "posted_date": date4,
        "source": "LinkedIn Jobs",
        "url": "https://www.linkedin.com/jobs/view/swiggy-qa-intern",
        "company_type": "Product-based"
    })
    jobs.append({
        "id": generate_job_id("Quality Assurance (QA) Internship", "Swiggy", "Bangalore", "Internshala"),
        "title": "Quality Assurance (QA) Internship",
        "company": "Swiggy",
        "location": "Bangalore",
        "experience_level": "0 yrs",
        "salary": "₹25,000 / month",
        "skills": ["Selenium", "Python", "Manual Testing"],
        "posted_date": date4,
        "source": "Internshala",
        "url": "https://internshala.com/internship/detail/swiggy-qa-intern-12",
        "company_type": "Product-based"
    })
    
    return jobs

def sync_all_jobs():
    """Aggregates jobs from Adzuna and Mock feeds, saves to DB, and runs deduplication."""
    # 1. Initialize DB if not done
    db.init_db()
    
    all_jobs = []
    
    # 2. Get Adzuna jobs
    print("Fetching jobs from Adzuna API...")
    adzuna_jobs = fetch_adzuna_jobs()
    all_jobs.extend(adzuna_jobs)
    
    # 3. Get Mock jobs
    print("Generating mock jobs...")
    mock_jobs = generate_mock_jobs()
    all_jobs.extend(mock_jobs)
    
    # 4. Save all to DB
    print(f"Saving {len(all_jobs)} jobs to the database...")
    for job in all_jobs:
        db.save_job(job)
        
    # 5. Run deduplication engine
    print("Running deduplication engine...")
    duplicates_count = run_deduplication()
    print(f"Deduplication complete. Flagged {duplicates_count} jobs as duplicates.")
    
    return {
        "total_fetched": len(all_jobs),
        "duplicates_detected": duplicates_count
    }
