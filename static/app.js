// State Management
let jobsState = [];
let statsState = {};
let activeFilters = {
    experience: new Set(),
    skills: new Set(),
    location: new Set(),
    company_type: new Set(),
    posted_within: ''
};
let searchQuery = '';
let bookmarksOnly = false;
let isSyncing = false;

// Predefined list of popular IT Skills for filter tags
const popularSkills = ["Python", "Java", "React", "JavaScript", "Node.js", "Django", "SQL", "Selenium", "HTML", "CSS", "QA"];

// Indian Startups Directory Dataset
const indianStartups = [
    { name: "Paytm", initials: "PT", industry: "Fintech", hq: "Noida", website: "https://paytm.com", careers: "https://jobs.paytm.com", gradient: "from-sky-500 to-blue-700", description: "India's leading digital payments platform powering mobile payments, banking, and financial services for millions." },
    { name: "Razorpay", initials: "RP", industry: "Fintech", hq: "Bengaluru", website: "https://razorpay.com", careers: "https://razorpay.com/careers", gradient: "from-blue-500 to-indigo-700", description: "Full-stack payments and banking platform for businesses, enabling seamless online transactions across India." },
    { name: "Zomato", initials: "ZM", industry: "Foodtech", hq: "Gurugram", website: "https://www.zomato.com", careers: "https://www.zomato.com/careers", gradient: "from-red-500 to-rose-700", description: "Leading food delivery and restaurant discovery platform connecting millions of users with their favourite restaurants." },
    { name: "Swiggy", initials: "SW", industry: "Foodtech", hq: "Bengaluru", website: "https://www.swiggy.com", careers: "https://careers.swiggy.com", gradient: "from-orange-400 to-orange-600", description: "On-demand convenience platform offering food delivery, grocery, and instant commerce through Instamart." },
    { name: "Cred", initials: "CR", industry: "Fintech", hq: "Bengaluru", website: "https://cred.club", careers: "https://careers.cred.club", gradient: "from-gray-100 to-gray-400", description: "Members-only credit card management app rewarding users for timely bill payments and financial discipline." },
    { name: "Flipkart", initials: "FK", industry: "E-commerce", hq: "Bengaluru", website: "https://www.flipkart.com", careers: "https://www.flipkartcareers.com", gradient: "from-yellow-400 to-blue-600", description: "India's homegrown e-commerce giant offering a vast marketplace for electronics, fashion, and daily essentials." },
    { name: "Ola Cabs", initials: "OL", industry: "Mobility", hq: "Bengaluru", website: "https://www.olacabs.com", careers: "https://www.olacabs.com/careers", gradient: "from-green-500 to-emerald-700", description: "Ride-hailing and electric vehicle company transforming urban mobility across India and international markets." },
    { name: "Zepto", initials: "ZP", industry: "Quick Commerce", hq: "Mumbai", website: "https://www.zeptonow.com", careers: "https://www.zeptonow.com/careers", gradient: "from-violet-500 to-purple-700", description: "Ultra-fast grocery delivery startup delivering essentials in 10 minutes, redefining quick commerce in India." },
    { name: "Groww", initials: "GW", industry: "Wealthtech", hq: "Bengaluru", website: "https://groww.in", careers: "https://groww.in/careers", gradient: "from-emerald-400 to-teal-600", description: "Democratizing investments by making stocks, mutual funds, and digital gold accessible to every Indian." },
    { name: "InMobi", initials: "IM", industry: "Adtech", hq: "Bengaluru", website: "https://www.inmobi.com", careers: "https://www.inmobi.com/company/careers", gradient: "from-cyan-500 to-blue-600", description: "Global mobile advertising and enterprise platform delivering AI-powered marketing solutions worldwide." },
    { name: "Freshworks", initials: "FW", industry: "SaaS", hq: "Chennai", website: "https://www.freshworks.com", careers: "https://www.freshworks.com/company/careers", gradient: "from-green-400 to-emerald-600", description: "Cloud-based SaaS company providing customer engagement, IT service, and HR management software globally." },
    { name: "Zoho", initials: "ZH", industry: "SaaS", hq: "Chennai", website: "https://www.zoho.com", careers: "https://careers.zoho.com", gradient: "from-red-500 to-yellow-500", description: "Privacy-first SaaS suite with 55+ business apps for CRM, email, project management, and more." },
    { name: "PhonePe", initials: "PP", industry: "Fintech", hq: "Bengaluru", website: "https://www.phonepe.com", careers: "https://www.phonepe.com/careers", gradient: "from-indigo-500 to-purple-600", description: "India's most-used UPI payments app enabling instant money transfers, bill payments, and investments." },
    { name: "Meesho", initials: "MS", industry: "Social Commerce", hq: "Bengaluru", website: "https://meesho.com", careers: "https://meesho.io/careers", gradient: "from-pink-500 to-rose-600", description: "Social commerce platform empowering small businesses and individuals to start zero-investment online stores." },
    { name: "Nykaa", initials: "NK", industry: "Beauty E-commerce", hq: "Mumbai", website: "https://www.nykaa.com", careers: "https://www.nykaa.com/careers", gradient: "from-pink-400 to-fuchsia-600", description: "India's leading beauty and lifestyle e-commerce platform offering premium cosmetics, wellness, and fashion." }
];

// DOM Elements
const searchInput = document.getElementById('search-input');
const clearSearchBtn = document.getElementById('clear-search');
const bookmarksToggleBtn = document.getElementById('bookmarks-toggle');
const bookmarksBadge = document.getElementById('bookmarks-badge');
const syncButton = document.getElementById('sync-button');
const syncIcon = document.getElementById('sync-icon');
const resetFiltersBtn = document.getElementById('reset-filters');
const skillsContainer = document.getElementById('skills-filter-container');
const jobsContainer = document.getElementById('jobs-container');
const countNumber = document.getElementById('count-number');
const toastContainer = document.getElementById('toast-container');

// Tab & Directory DOM Elements
const tabJobs = document.getElementById('tab-jobs');
const tabStartups = document.getElementById('tab-startups');
const jobsViewSection = document.getElementById('jobs-view-section');
const startupsViewSection = document.getElementById('startups-view-section');
const startupsContainer = document.getElementById('startups-container');

// Stats Counters
const statTotalJobs = document.getElementById('stat-total-jobs');
const statNewToday = document.getElementById('stat-new-today');
const statDuplicates = document.getElementById('stat-duplicates');
const statBookmarked = document.getElementById('stat-bookmarked');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    renderSkillsFilters();
    bindEvents();
    bindTabEvents();
    renderStartupDirectory();
    
    // Initial fetch (if database is empty, we will show a clean empty state prompting to sync)
    fetchStats();
    fetchJobs();
});

// Render dynamic skill selection pills in the sidebar
function renderSkillsFilters() {
    skillsContainer.innerHTML = '';
    popularSkills.forEach(skill => {
        const pill = document.createElement('button');
        pill.innerText = skill;
        pill.className = 'px-2.5 py-1 text-xs rounded-lg border border-white/10 text-gray-300 hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all duration-200';
        pill.dataset.skill = skill;
        
        pill.addEventListener('click', () => {
            if (activeFilters.skills.has(skill)) {
                activeFilters.skills.delete(skill);
                pill.classList.remove('bg-indigo-500/20', 'text-indigo-300', 'border-indigo-500/40');
            } else {
                activeFilters.skills.add(skill);
                pill.classList.add('bg-indigo-500/20', 'text-indigo-300', 'border-indigo-500/40');
            }
            fetchJobs();
        });
        skillsContainer.appendChild(pill);
    });
}

// Bind Event Listeners
function bindEvents() {
    // Search with debounce
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.trim();
        if (searchQuery) {
            clearSearchBtn.classList.remove('hidden');
        } else {
            clearSearchBtn.classList.add('hidden');
        }
        
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            fetchJobs();
        }, 300);
    });

    clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchQuery = '';
        clearSearchBtn.classList.add('hidden');
        fetchJobs();
    });

    // Bookmarks Page Toggle
    bookmarksToggleBtn.addEventListener('click', () => {
        bookmarksOnly = !bookmarksOnly;
        if (bookmarksOnly) {
            bookmarksToggleBtn.classList.add('bg-indigo-500/20', 'border-indigo-500', 'text-indigo-400');
            bookmarksToggleBtn.querySelector('i').className = 'fa-solid fa-bookmark text-indigo-400';
            showToast("Showing saved bookmarks only", "info");
        } else {
            bookmarksToggleBtn.classList.remove('bg-indigo-500/20', 'border-indigo-500', 'text-indigo-400');
            bookmarksToggleBtn.querySelector('i').className = 'fa-regular fa-bookmark text-gray-300';
        }
        fetchJobs();
    });

    // Sync button
    syncButton.addEventListener('click', triggerSync);

    // Sidebar Filters Checkboxes & Radios
    document.querySelectorAll('input[name="experience"]').forEach(chk => {
        chk.addEventListener('change', () => {
            if (chk.checked) activeFilters.experience.add(chk.value);
            else activeFilters.experience.delete(chk.value);
            fetchJobs();
        });
    });

    document.querySelectorAll('input[name="location"]').forEach(chk => {
        chk.addEventListener('change', () => {
            if (chk.checked) activeFilters.location.add(chk.value);
            else activeFilters.location.delete(chk.value);
            fetchJobs();
        });
    });

    document.querySelectorAll('input[name="company_type"]').forEach(chk => {
        chk.addEventListener('change', () => {
            if (chk.checked) activeFilters.company_type.add(chk.value);
            else activeFilters.company_type.delete(chk.value);
            fetchJobs();
        });
    });

    document.querySelectorAll('input[name="posted_within"]').forEach(rad => {
        rad.addEventListener('change', () => {
            activeFilters.posted_within = rad.value;
            fetchJobs();
        });
    });

    // Reset Filters
    resetFiltersBtn.addEventListener('click', () => {
        // Reset checkbox states
        document.querySelectorAll('input[type="checkbox"]').forEach(chk => chk.checked = false);
        // Reset radio states
        document.querySelector('input[name="posted_within"][value=""]').checked = true;
        // Reset state sets
        activeFilters.experience.clear();
        activeFilters.location.clear();
        activeFilters.company_type.clear();
        activeFilters.skills.clear();
        activeFilters.posted_within = '';
        
        // Reset skill pill classes
        document.querySelectorAll('#skills-filter-container button').forEach(btn => {
            btn.classList.remove('bg-indigo-500/20', 'text-indigo-300', 'border-indigo-500/40');
        });
        
        fetchJobs();
        showToast("All filters reset", "info");
    });
}

// Fetch dashboard statistics
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        if (data.status === 'success') {
            statsState = data.stats;
            updateStatsUI();
        }
    } catch (error) {
        console.error("Error fetching stats:", error);
    }
}

// Update counters on stats cards
function updateStatsUI() {
    statTotalJobs.textContent = statsState.total_active_jobs !== undefined ? statsState.total_active_jobs : '0';
    statNewToday.textContent = statsState.new_today !== undefined ? statsState.new_today : '0';
    statDuplicates.textContent = statsState.total_duplicates !== undefined ? statsState.total_duplicates : '0';
    statBookmarked.textContent = statsState.bookmarked !== undefined ? statsState.bookmarked : '0';
    
    // Update bookmarks badge
    if (statsState.bookmarked > 0) {
        bookmarksBadge.textContent = statsState.bookmarked;
        bookmarksBadge.classList.remove('hidden');
    } else {
        bookmarksBadge.classList.add('hidden');
    }
}

// Fetch filtered jobs from API
async function fetchJobs() {
    renderLoadingState();
    
    // Construct Query String
    let queryParams = [];
    
    if (searchQuery) queryParams.push(`search=${encodeURIComponent(searchQuery)}`);
    
    if (activeFilters.experience.size > 0) {
        queryParams.push(`experience=${encodeURIComponent(Array.from(activeFilters.experience).join(','))}`);
    }
    
    if (activeFilters.skills.size > 0) {
        queryParams.push(`skills=${encodeURIComponent(Array.from(activeFilters.skills).join(','))}`);
    }
    
    if (activeFilters.location.size > 0) {
        queryParams.push(`locations=${encodeURIComponent(Array.from(activeFilters.location).join(','))}`);
    }
    
    if (activeFilters.company_type.size > 0) {
        queryParams.push(`company_types=${encodeURIComponent(Array.from(activeFilters.company_type).join(','))}`);
    }
    
    if (activeFilters.posted_within) {
        queryParams.push(`posted_within=${activeFilters.posted_within}`);
    }
    
    if (bookmarksOnly) {
        queryParams.push(`bookmarks_only=true`);
    }
    
    const queryString = queryParams.length > 0 ? `?${queryParams.join('&')}` : '';
    
    try {
        const response = await fetch(`/api/jobs${queryString}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            jobsState = data.jobs;
            countNumber.textContent = data.count;
            renderJobsList();
        } else {
            renderEmptyState("Database query error.");
        }
    } catch (error) {
        console.error("Error fetching jobs:", error);
        renderEmptyState("Unable to connect to the backend server.");
    }
}

// Render skeleton card loaders while fetching
function renderLoadingState() {
    jobsContainer.innerHTML = '';
    countNumber.textContent = '-';
    
    for (let i = 0; i < 3; i++) {
        const skeleton = document.createElement('div');
        skeleton.className = 'glass-panel rounded-2xl p-5 flex flex-col gap-4 animate-pulse';
        skeleton.innerHTML = `
            <div class="flex justify-between items-start">
                <div class="space-y-2.5 w-2/3">
                    <div class="h-5 w-3/4 shimmer rounded"></div>
                    <div class="h-4 w-1/2 shimmer rounded"></div>
                </div>
                <div class="h-8 w-20 shimmer rounded-xl"></div>
            </div>
            <div class="flex gap-2 py-1">
                <div class="h-6 w-16 shimmer rounded-lg"></div>
                <div class="h-6 w-24 shimmer rounded-lg"></div>
                <div class="h-6 w-20 shimmer rounded-lg"></div>
            </div>
            <div class="flex gap-2">
                <div class="h-5 w-12 shimmer rounded-md"></div>
                <div class="h-5 w-12 shimmer rounded-md"></div>
                <div class="h-5 w-12 shimmer rounded-md"></div>
            </div>
            <div class="h-px bg-white/5 w-full"></div>
            <div class="flex justify-between items-center">
                <div class="h-4 w-24 shimmer rounded"></div>
                <div class="h-9 w-28 shimmer rounded-xl"></div>
            </div>
        `;
        jobsContainer.appendChild(skeleton);
    }
}

// Render a clean empty state
function renderEmptyState(message) {
    jobsContainer.innerHTML = `
        <div class="glass-panel rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-4 fade-in-item">
            <div class="w-16 h-16 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center text-3xl">
                <i class="fa-solid fa-folder-open"></i>
            </div>
            <div>
                <h3 class="text-lg font-semibold text-white">No job openings found</h3>
                <p class="text-sm text-gray-400 mt-1 max-w-sm mx-auto">${message || "Try adjusting your search criteria or click 'Sync Aggregator' to fetch new job postings."}</p>
            </div>
            ${!jobsState.length ? `
                <button onclick="document.getElementById('sync-button').click()" class="mt-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-md shadow-indigo-500/20 transition-all">
                    <i class="fa-solid fa-rotate text-xs mr-2"></i> Sync Jobs Now
                </button>
            ` : ''}
        </div>
    `;
}

// Color badges based on platform source
function getSourceBadgeClass(source) {
    const src = source.toLowerCase();
    if (src.includes('linkedin')) return 'badge-indigo';
    if (src.includes('naukri')) return 'bg-amber-500/10 text-amber-400 border border-amber-500/30';
    if (src.includes('indeed')) return 'badge-cyan';
    if (src.includes('internshala')) return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30';
    if (src.includes('wellfound')) return 'bg-gray-100/10 text-gray-100 border border-gray-100/30';
    if (src.includes('foundit')) return 'badge-accent';
    return 'badge-indigo';
}

// Render full list of job cards
function renderJobsList() {
    jobsContainer.innerHTML = '';
    
    if (jobsState.length === 0) {
        renderEmptyState(
            bookmarksOnly 
                ? "You haven't bookmarked any jobs yet. Browse listings and click the bookmark star to save them."
                : "No job matches your filters. Try removing some filters or updating search terms."
        );
        return;
    }
    
    jobsState.forEach((job, index) => {
        const card = document.createElement('div');
        card.className = `glass-panel glass-panel-hover rounded-2xl p-5 flex flex-col gap-4 fade-in-item`;
        card.style.animationDelay = `${index * 50}ms`;
        
        // Check if job is freshly posted today
        const isNewToday = isJobNew(job.posted_date);
        
        // Generate skill pill HTML
        const skillsHTML = job.skills.map(skill => `
            <span class="px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded bg-slate-900 border border-white/5 text-gray-400">${skill}</span>
        `).join('');
        
        // Generate duplicate listings details
        let duplicateHTML = '';
        if (job.duplicates && job.duplicates.length > 0) {
            const alternativeLinks = job.duplicates.map(d => `
                <a href="${d.url}" target="_blank" class="hover:text-indigo-400 transition-colors underline flex items-center gap-1">
                    ${d.source} <i class="fa-solid fa-arrow-up-right-from-square text-[8px]"></i>
                </a>
            `).join(', ');
            
            duplicateHTML = `
                <div class="mt-1.5 px-3 py-2 rounded-xl bg-indigo-500/5 border border-indigo-500/10 text-xs text-indigo-300/80 flex items-center gap-2">
                    <i class="fa-solid fa-copy text-[10px] text-indigo-400"></i>
                    <span>Aggregated duplicate postings: ${alternativeLinks}</span>
                </div>
            `;
        }
        
        card.innerHTML = `
            <div class="flex justify-between items-start gap-4">
                <div class="space-y-1">
                    <div class="flex items-center flex-wrap gap-2">
                        <h3 class="text-base sm:text-lg font-bold text-white tracking-tight">${job.title}</h3>
                        ${isNewToday ? `<span class="px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-widest badge-green rounded-full shadow-sm shadow-emerald-500/10">New Today</span>` : ''}
                    </div>
                    <p class="text-sm text-gray-300 font-medium">${job.company} <span class="text-gray-500 px-1">•</span> <span class="text-gray-400">${job.location}</span></p>
                </div>
                
                <span class="px-2.5 py-1 text-xs font-bold rounded-lg ${getSourceBadgeClass(job.source)} flex items-center gap-1.5 flex-shrink-0">
                    <i class="fa-solid fa-share-nodes text-[10px]"></i> ${job.source}
                </span>
            </div>
            
            <div class="flex flex-wrap gap-2 text-xs">
                <span class="px-2.5 py-1 rounded-xl bg-white/5 text-gray-300 flex items-center gap-1.5">
                    <i class="fa-solid fa-graduation-cap text-indigo-400"></i> ${job.experience_level}
                </span>
                <span class="px-2.5 py-1 rounded-xl bg-white/5 text-gray-300 flex items-center gap-1.5">
                    <i class="fa-solid fa-wallet text-indigo-400"></i> ${job.salary || 'Not Disclosed'}
                </span>
                <span class="px-2.5 py-1 rounded-xl bg-white/5 text-gray-300 flex items-center gap-1.5">
                    <i class="fa-solid fa-building text-indigo-400"></i> ${job.company_type || 'Startup'}
                </span>
            </div>
            
            <div class="flex flex-wrap gap-1.5 items-center">
                ${skillsHTML}
            </div>
            
            ${duplicateHTML}
            
            <div class="h-px bg-white/5 w-full"></div>
            
            <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400 flex items-center gap-1.5">
                    <i class="fa-solid fa-clock text-[10px]"></i> Posted: ${formatDate(job.posted_date)}
                </span>
                
                <div class="flex items-center gap-3">
                    <!-- Bookmark Trigger -->
                    <button 
                        class="w-9 h-9 rounded-xl border border-white/5 hover:border-indigo-500/40 flex items-center justify-center transition-all bookmark-btn"
                        data-id="${job.id}"
                        title="${job.is_bookmarked ? 'Remove Bookmark' : 'Save for Later'}"
                    >
                        <i class="${job.is_bookmarked ? 'fa-solid fa-bookmark text-indigo-400' : 'fa-regular fa-bookmark text-gray-400 hover:text-white'}"></i>
                    </button>
                    
                    <a 
                        href="${job.url}" 
                        target="_blank" 
                        class="h-9 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
                    >
                        Apply Direct <i class="fa-solid fa-chevron-right text-[10px]"></i>
                    </a>
                </div>
            </div>
        `;
        
        // Hook Bookmark toggle click
        card.querySelector('.bookmark-btn').addEventListener('click', (e) => {
            const btn = e.currentTarget;
            const jobId = btn.dataset.id;
            toggleBookmark(jobId, btn);
        });
        
        jobsContainer.appendChild(card);
    });
}

// Check if a date string is today (latest 24 hours)
function isJobNew(dateString) {
    const today = new Date().toISOString().split('T')[0];
    return dateString === today;
}

// Convert YYYY-MM-DD into a readable format: e.g. "Today" or "July 21, 2026"
function formatDate(dateString) {
    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
    
    if (dateString === today) return "Today";
    if (dateString === yesterday) return "Yesterday";
    
    const parts = dateString.split('-');
    if (parts.length === 3) {
        const dateObj = new Date(parts[0], parts[1] - 1, parts[2]);
        return dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
    return dateString;
}

// Asynchronously bookmark a job
async function toggleBookmark(jobId, buttonElement) {
    try {
        const response = await fetch(`/api/jobs/${jobId}/bookmark`, { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'success') {
            const isBookmarked = data.is_bookmarked;
            
            // Show toast notification
            showToast(data.message, "success");
            
            // Refresh stats in background
            fetchStats();
            
            // Adjust Bookmark Icon Class
            const icon = buttonElement.querySelector('i');
            if (isBookmarked) {
                icon.className = 'fa-solid fa-bookmark text-indigo-400';
                buttonElement.title = 'Remove Bookmark';
            } else {
                icon.className = 'fa-regular fa-bookmark text-gray-400 hover:text-white';
                buttonElement.title = 'Save for Later';
                
                // If we are currently in Bookmarks-only view mode, remove the card dynamically
                if (bookmarksOnly) {
                    buttonElement.closest('.glass-panel').remove();
                    // Update results label count
                    const currentCount = parseInt(countNumber.textContent, 10);
                    countNumber.textContent = Math.max(0, currentCount - 1);
                    if (currentCount - 1 === 0) {
                        renderEmptyState("You haven't bookmarked any jobs yet.");
                    }
                }
            }
        }
    } catch (error) {
        console.error("Error toggling bookmark:", error);
        showToast("Failed to save bookmark", "error");
    }
}

// Trigger Backend Feed Synchronization
async function triggerSync() {
    if (isSyncing) return;
    
    isSyncing = true;
    syncButton.disabled = true;
    syncButton.classList.add('opacity-70', 'cursor-not-allowed');
    syncIcon.classList.add('animate-spin');
    showToast("Connecting to feeds & scraping portals...", "info");
    
    try {
        const response = await fetch('/api/jobs/sync', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(`Sync complete! Loaded ${data.synced_count} jobs. Prevented ${data.duplicates_detected} duplicates.`, "success");
            
            // Reload database state
            statsState = data.stats;
            updateStatsUI();
            fetchJobs();
        } else {
            showToast("Synchronization failed", "error");
        }
    } catch (error) {
        console.error("Error syncing:", error);
        showToast("Error connecting to feed aggregator service", "error");
    } finally {
        isSyncing = false;
        syncButton.disabled = false;
        syncButton.classList.remove('opacity-70', 'cursor-not-allowed');
        syncIcon.classList.remove('animate-spin');
    }
}

// Show animated glassmorphic notification toast
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = 'toast-notification px-4 py-3 rounded-xl glass-panel shadow-2xl flex items-center gap-3 border border-white/10 text-sm max-w-sm transition-all duration-300';
    
    let iconHTML = '';
    if (type === 'success') {
        iconHTML = `<div class="w-6 h-6 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center flex-shrink-0 text-xs"><i class="fa-solid fa-check"></i></div>`;
    } else if (type === 'error') {
        iconHTML = `<div class="w-6 h-6 rounded-full bg-red-500/10 text-red-400 flex items-center justify-center flex-shrink-0 text-xs"><i class="fa-solid fa-xmark"></i></div>`;
    } else {
        iconHTML = `<div class="w-6 h-6 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center flex-shrink-0 text-xs"><i class="fa-solid fa-info"></i></div>`;
    }
    
    toast.innerHTML = `
        ${iconHTML}
        <span class="text-gray-200 font-medium">${message}</span>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 3.5 seconds
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3500);
}

// ==========================================
// Tab Switching & Startup Directory
// ==========================================

function bindTabEvents() {
    tabJobs.addEventListener('click', () => switchTab('jobs'));
    tabStartups.addEventListener('click', () => switchTab('startups'));
}

function switchTab(tab) {
    if (tab === 'jobs') {
        tabJobs.classList.add('active');
        tabJobs.setAttribute('aria-selected', 'true');
        tabStartups.classList.remove('active');
        tabStartups.setAttribute('aria-selected', 'false');
        jobsViewSection.classList.remove('hidden');
        startupsViewSection.classList.add('hidden');
    } else {
        tabStartups.classList.add('active');
        tabStartups.setAttribute('aria-selected', 'true');
        tabJobs.classList.remove('active');
        tabJobs.setAttribute('aria-selected', 'false');
        startupsViewSection.classList.remove('hidden');
        jobsViewSection.classList.add('hidden');
    }
}

function searchJobsByCompany(companyName) {
    // Switch back to Jobs tab
    switchTab('jobs');

    // Fill the search input and trigger a fetch
    searchInput.value = companyName;
    searchQuery = companyName;
    clearSearchBtn.classList.remove('hidden');
    fetchJobs();
    showToast(`Filtering jobs for "${companyName}"`, 'info');
}

function renderStartupDirectory() {
    startupsContainer.innerHTML = '';

    indianStartups.forEach((startup, index) => {
        const card = document.createElement('div');
        card.className = 'glass-panel rounded-2xl p-6 flex flex-col gap-4 startup-card fade-in-item';
        card.style.animationDelay = `${index * 60}ms`;

        card.innerHTML = `
            <div class="flex items-start gap-4">
                <div class="w-14 h-14 flex-shrink-0 startup-avatar bg-gradient-to-br ${startup.gradient}">
                    ${startup.initials}
                </div>
                <div class="flex-grow min-w-0">
                    <h3 class="text-lg font-bold text-white tracking-tight truncate">${startup.name}</h3>
                    <div class="flex flex-wrap items-center gap-2 mt-1">
                        <span class="px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">${startup.industry}</span>
                        <span class="text-xs text-gray-400 flex items-center gap-1"><i class="fa-solid fa-location-dot text-[9px]"></i> ${startup.hq}</span>
                    </div>
                </div>
            </div>

            <p class="text-xs text-gray-400 leading-relaxed line-clamp-3">${startup.description}</p>

            <div class="h-px bg-white/5 w-full"></div>

            <div class="flex flex-wrap items-center gap-2">
                <a href="${startup.website}" target="_blank" rel="noopener noreferrer"
                   class="h-8 px-3 rounded-lg border border-white/10 hover:border-indigo-500/40 text-gray-300 hover:text-white text-[11px] font-medium flex items-center gap-1.5 transition-all">
                    <i class="fa-solid fa-globe text-[10px] text-indigo-400"></i> Website
                </a>
                <a href="${startup.careers}" target="_blank" rel="noopener noreferrer"
                   class="h-8 px-3 rounded-lg border border-white/10 hover:border-emerald-500/40 text-gray-300 hover:text-white text-[11px] font-medium flex items-center gap-1.5 transition-all">
                    <i class="fa-solid fa-briefcase text-[10px] text-emerald-400"></i> Careers
                </a>
                <button onclick="searchJobsByCompany('${startup.name}')" 
                   class="h-8 px-3 rounded-lg startup-search-btn text-white text-[11px] font-semibold flex items-center gap-1.5">
                    <i class="fa-solid fa-magnifying-glass text-[10px]"></i> Search Jobs
                </button>
            </div>
        `;

        startupsContainer.appendChild(card);
    });
}
