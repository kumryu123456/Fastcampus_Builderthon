/**
 * Job Discovery UI Logic - PathPilot
 * T059-T063: Frontend JavaScript for job discovery
 * API_BASE_URL is defined in config.js
 */

// Tab Elements
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Recommendations Tab Elements
const recResumeSelect = document.getElementById('rec-resume-select');
const recLocation = document.getElementById('rec-location');
const recJobType = document.getElementById('rec-job-type');
const recExperience = document.getElementById('rec-experience');
const recIndustry = document.getElementById('rec-industry');
const getRecommendationsBtn = document.getElementById('get-recommendations-btn');
const recLoading = document.getElementById('rec-loading');
const recError = document.getElementById('rec-error');
const recErrorText = document.getElementById('rec-error-text');
const recommendationsResults = document.getElementById('recommendations-results');
const recommendationsList = document.getElementById('recommendations-list');

// Match Tab Elements
const matchResumeSelect = document.getElementById('match-resume-select');
const matchJobTitle = document.getElementById('match-job-title');
const matchCompany = document.getElementById('match-company');
const matchDescription = document.getElementById('match-description');
const analyzeMatchBtn = document.getElementById('analyze-match-btn');
const matchLoading = document.getElementById('match-loading');
const matchError = document.getElementById('match-error');
const matchErrorText = document.getElementById('match-error-text');
const matchResults = document.getElementById('match-results');

// Saved Jobs Elements
const savedJobsList = document.getElementById('saved-jobs-list');

// State
let currentResumeId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupEventListeners();
    loadResumes();
    loadSavedJobs();
});

/**
 * Setup tab navigation
 */
function setupTabs() {
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;

            // Update buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${tabId}-tab`) {
                    content.classList.add('active');
                }
            });
        });
    });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    getRecommendationsBtn.addEventListener('click', getRecommendations);
    analyzeMatchBtn.addEventListener('click', analyzeMatch);
}

/**
 * Load user's analyzed resumes
 */
async function loadResumes() {
    // For MVP, we'll use a simple approach - check if resume ID 11 exists
    // In production, this would fetch from /api/v1/resume/list endpoint
    try {
        // Try to get the most recent resume
        const response = await fetch(`${API_BASE_URL}/resume/11/analysis`);
        if (response.ok) {
            const data = await response.json();
            addResumeOption(recResumeSelect, data.resume_id, data.original_filename);
            addResumeOption(matchResumeSelect, data.resume_id, data.original_filename);
        }
    } catch (error) {
        console.log('No resumes found or error loading:', error);
    }

    // Also try lower IDs
    for (let id = 1; id <= 10; id++) {
        try {
            const response = await fetch(`${API_BASE_URL}/resume/${id}/analysis`);
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'analyzed') {
                    addResumeOption(recResumeSelect, data.resume_id, data.original_filename);
                    addResumeOption(matchResumeSelect, data.resume_id, data.original_filename);
                }
            }
        } catch (error) {
            // Ignore errors for non-existent resumes
        }
    }
}

/**
 * Add resume option to select
 */
function addResumeOption(select, id, filename) {
    // Check if option already exists
    if (select.querySelector(`option[value="${id}"]`)) return;

    const option = document.createElement('option');
    option.value = id;
    option.textContent = `${filename} (ID: ${id})`;
    select.appendChild(option);
}

/**
 * Load saved jobs
 */
async function loadSavedJobs() {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/saved`);
        if (response.ok) {
            const data = await response.json();
            displaySavedJobs(data.jobs);
        }
    } catch (error) {
        console.error('Error loading saved jobs:', error);
    }
}

/**
 * Get AI recommendations
 */
async function getRecommendations() {
    const resumeId = recResumeSelect.value;

    if (!resumeId) {
        showError(recError, recErrorText, 'Please select a resume first.');
        return;
    }

    // Show loading
    getRecommendationsBtn.style.display = 'none';
    recLoading.style.display = 'block';
    hideError(recError);
    recommendationsResults.style.display = 'none';

    try {
        const requestBody = {
            resume_id: parseInt(resumeId),
            location: recLocation.value || null,
            job_type: recJobType.value || null,
            experience_level: recExperience.value || null,
            industry: recIndustry.value || null,
            limit: 10,
        };

        const response = await fetch(`${API_BASE_URL}/jobs/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.message || 'Failed to get recommendations');
        }

        const data = await response.json();

        // Display results
        displayRecommendations(data.recommendations);

    } catch (error) {
        console.error('Recommendations error:', error);
        showError(recError, recErrorText, error.message);
    } finally {
        recLoading.style.display = 'none';
        getRecommendationsBtn.style.display = 'block';
    }
}

/**
 * Display recommendations
 */
function displayRecommendations(recommendations) {
    recommendationsList.innerHTML = '';

    if (!recommendations || recommendations.length === 0) {
        recommendationsList.innerHTML = '<p class="no-data">No recommendations found.</p>';
        recommendationsResults.style.display = 'block';
        return;
    }

    recommendations.forEach(rec => {
        const card = createJobCard(rec);
        recommendationsList.appendChild(card);
    });

    recommendationsResults.style.display = 'block';
    recommendationsResults.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Create job recommendation card
 */
function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';

    const matchClass = job.match_score >= 85 ? 'high' : job.match_score >= 70 ? 'medium' : 'low';

    card.innerHTML = `
        <div class="job-card-header">
            <div>
                <h3 class="job-card-title">${job.title}</h3>
                <p class="job-card-company">${job.company_type} - ${job.industry}</p>
            </div>
            <span class="match-badge ${matchClass}">${job.match_score}% Match</span>
        </div>

        <div class="job-card-meta">
            <span class="job-tag">${job.location}</span>
            <span class="job-tag">${job.job_type}</span>
            <span class="job-tag">${job.experience_level}</span>
        </div>

        <p class="job-card-reason">${job.match_reason}</p>

        ${job.matching_skills && job.matching_skills.length > 0 ? `
        <div class="job-card-skills">
            <h5>Your Matching Skills</h5>
            <div class="skill-tags">
                ${job.matching_skills.slice(0, 5).map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
            </div>
        </div>
        ` : ''}

        ${job.skills_to_develop && job.skills_to_develop.length > 0 ? `
        <div class="job-card-skills">
            <h5>Skills to Develop</h5>
            <div class="skill-tags">
                ${job.skills_to_develop.slice(0, 3).map(skill => `<span class="skill-tag missing">${skill}</span>`).join('')}
            </div>
        </div>
        ` : ''}

        ${job.sample_companies && job.sample_companies.length > 0 ? `
        <p class="job-card-companies">
            <strong>Sample Companies:</strong> ${job.sample_companies.join(', ')}
        </p>
        ` : ''}
    `;

    return card;
}

/**
 * Analyze job match
 */
async function analyzeMatch() {
    const resumeId = matchResumeSelect.value;
    const jobTitle = matchJobTitle.value.trim();
    const description = matchDescription.value.trim();

    if (!resumeId) {
        showError(matchError, matchErrorText, 'Please select a resume.');
        return;
    }

    if (!jobTitle) {
        showError(matchError, matchErrorText, 'Please enter a job title.');
        return;
    }

    if (!description || description.length < 50) {
        showError(matchError, matchErrorText, 'Please enter a more detailed job description (at least 50 characters).');
        return;
    }

    // Show loading
    analyzeMatchBtn.style.display = 'none';
    matchLoading.style.display = 'block';
    hideError(matchError);
    matchResults.style.display = 'none';

    try {
        const requestBody = {
            resume_id: parseInt(resumeId),
            job_title: jobTitle,
            job_description: description,
            company: matchCompany.value.trim() || null,
        };

        const response = await fetch(`${API_BASE_URL}/jobs/match`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.message || 'Match analysis failed');
        }

        const data = await response.json();

        // Display results
        displayMatchResults(data);

    } catch (error) {
        console.error('Match error:', error);
        showError(matchError, matchErrorText, error.message);
    } finally {
        matchLoading.style.display = 'none';
        analyzeMatchBtn.style.display = 'block';
    }
}

/**
 * Display match results
 */
function displayMatchResults(data) {
    const analysis = data.analysis;

    // Update score
    document.getElementById('match-score-value').textContent = analysis.match_score;
    document.getElementById('match-job-title-display').textContent = data.job_title;
    document.getElementById('match-level-display').textContent = analysis.match_level;

    // Update score circle color based on score
    const scoreCircle = document.querySelector('.match-score-circle');
    if (analysis.match_score >= 85) {
        scoreCircle.style.background = 'linear-gradient(135deg, #10b981, #059669)';
    } else if (analysis.match_score >= 70) {
        scoreCircle.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
    } else {
        scoreCircle.style.background = 'linear-gradient(135deg, #6b7280, #4b5563)';
    }

    // Matching skills
    const matchingSkillsDiv = document.getElementById('matching-skills');
    matchingSkillsDiv.innerHTML = analysis.matching_skills && analysis.matching_skills.length > 0
        ? analysis.matching_skills.map(s => `<span class="skill-tag">${s}</span>`).join('')
        : '<span class="no-data">None identified</span>';

    // Missing skills
    const missingSkillsDiv = document.getElementById('missing-skills');
    missingSkillsDiv.innerHTML = analysis.missing_skills && analysis.missing_skills.length > 0
        ? analysis.missing_skills.map(s => `<span class="skill-tag missing">${s}</span>`).join('')
        : '<span class="no-data">None - great match!</span>';

    // Relevant strengths
    const strengthsList = document.getElementById('relevant-strengths');
    strengthsList.innerHTML = analysis.relevant_strengths && analysis.relevant_strengths.length > 0
        ? analysis.relevant_strengths.map(s => `<li>${s}</li>`).join('')
        : '<li class="no-data">None identified</li>';

    // Recommendation
    document.getElementById('match-recommendation').textContent =
        analysis.recommendation || 'Please review the job requirements carefully.';

    // Show results
    matchResults.style.display = 'block';
    matchResults.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Display saved jobs
 */
function displaySavedJobs(jobs) {
    if (!jobs || jobs.length === 0) {
        savedJobsList.innerHTML = '<p class="no-data">No saved jobs yet. Get recommendations or analyze job matches to save jobs.</p>';
        return;
    }

    savedJobsList.innerHTML = jobs.map(job => `
        <div class="job-card">
            <div class="job-card-header">
                <div>
                    <h3 class="job-card-title">${job.title}</h3>
                    <p class="job-card-company">${job.company}</p>
                </div>
                ${job.match_score ? `<span class="match-badge">${job.match_score}%</span>` : ''}
            </div>
            <div class="job-card-meta">
                ${job.location ? `<span class="job-tag">${job.location}</span>` : ''}
                ${job.job_type ? `<span class="job-tag">${job.job_type}</span>` : ''}
                <span class="job-tag">${job.source}</span>
            </div>
        </div>
    `).join('');
}

/**
 * Show error message
 */
function showError(errorDiv, textSpan, message) {
    textSpan.textContent = message;
    errorDiv.style.display = 'flex';
}

/**
 * Hide error message
 */
function hideError(errorDiv) {
    errorDiv.style.display = 'none';
}
