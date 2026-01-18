/**
 * Dashboard Logic - PathPilot
 * Loads stats and displays user progress
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Load stats on page load
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
});

async function loadDashboardStats() {
    try {
        // Load resume count
        const resumeCount = await fetchCount('/resume/count');
        updateStat('resume-count', resumeCount);

        // Load cover letter count
        const letterCount = await fetchCount('/cover-letter/count');
        updateStat('letter-count', letterCount);

        // Load job count
        const jobCount = await fetchCount('/jobs/count');
        updateStat('job-count', jobCount);

        // Load interview count
        const interviewCount = await fetchCount('/interview/count');
        updateStat('interview-count', interviewCount);

    } catch (error) {
        console.log('Stats loading skipped (API may not support count endpoints)');
        // Set defaults if API doesn't support counts
        setDefaultStats();
    }
}

async function fetchCount(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        if (response.ok) {
            const data = await response.json();
            return data.count || 0;
        }
        return 0;
    } catch {
        return 0;
    }
}

function updateStat(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function setDefaultStats() {
    // Try to get actual counts from list endpoints
    fetchListCounts();
}

async function fetchListCounts() {
    try {
        // Resume count from list
        const resumeRes = await fetch(`${API_BASE_URL}/cover-letter/?limit=100`);
        if (resumeRes.ok) {
            const data = await resumeRes.json();
            updateStat('letter-count', data.cover_letters?.length || data.count || 0);
        }
    } catch {
        updateStat('letter-count', 0);
    }

    try {
        // Interview count from list
        const interviewRes = await fetch(`${API_BASE_URL}/interview/?limit=100`);
        if (interviewRes.ok) {
            const data = await interviewRes.json();
            updateStat('interview-count', data.interviews?.length || data.count || 0);
        }
    } catch {
        updateStat('interview-count', 0);
    }

    // Set others to 0 for now
    updateStat('resume-count', 0);
    updateStat('job-count', 0);
}
