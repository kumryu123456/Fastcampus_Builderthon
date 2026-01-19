/**
 * Applications Tracker Logic - PathPilot
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

// DOM Elements
const applicationsTable = document.getElementById('applications-tbody');
const emptyState = document.getElementById('empty-state');
const loadingState = document.getElementById('loading-state');
const statusFilter = document.getElementById('status-filter');
const addApplicationBtn = document.getElementById('add-application-btn');
const applicationModal = document.getElementById('application-modal');
const applicationForm = document.getElementById('application-form');
const detailModal = document.getElementById('detail-modal');

// State
let applications = [];
let currentApplicationId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadApplications();
    loadStats();
    setupEventListeners();
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Add application button
    addApplicationBtn.addEventListener('click', () => openModal());

    // Filter change
    statusFilter.addEventListener('change', () => loadApplications());

    // Modal close buttons
    document.getElementById('close-modal').addEventListener('click', closeModal);
    document.getElementById('cancel-btn').addEventListener('click', closeModal);
    document.getElementById('close-detail-modal').addEventListener('click', closeDetailModal);

    // Modal backdrop click
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.addEventListener('click', () => {
            closeModal();
            closeDetailModal();
        });
    });

    // Form submit
    applicationForm.addEventListener('submit', handleFormSubmit);

    // Edit from detail
    document.getElementById('edit-from-detail-btn').addEventListener('click', () => {
        closeDetailModal();
        if (currentApplicationId) {
            const app = applications.find(a => a.id === currentApplicationId);
            if (app) openModal(app);
        }
    });

    // Delete from detail
    document.getElementById('delete-from-detail-btn').addEventListener('click', () => {
        if (currentApplicationId && confirm('Are you sure you want to delete this application?')) {
            deleteApplication(currentApplicationId);
            closeDetailModal();
        }
    });
}

/**
 * Load applications from API
 */
async function loadApplications() {
    showLoading();

    try {
        const status = statusFilter.value;
        const url = status
            ? `${API_BASE_URL}/applications/?status=${status}`
            : `${API_BASE_URL}/applications/`;

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load applications');

        const data = await response.json();
        applications = data.applications;

        renderApplications();
    } catch (error) {
        console.error('Load error:', error);
        showError('Failed to load applications');
    }
}

/**
 * Load statistics
 */
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/applications/stats`);
        if (!response.ok) throw new Error('Failed to load stats');

        const stats = await response.json();

        document.getElementById('stat-total').textContent = stats.total || 0;
        document.getElementById('stat-active').textContent = stats.active || 0;
        document.getElementById('stat-interview').textContent = stats.by_status?.interview || 0;
        document.getElementById('stat-offer').textContent = stats.by_status?.offer || 0;
    } catch (error) {
        console.error('Stats error:', error);
    }
}

/**
 * Render applications table
 */
function renderApplications() {
    hideLoading();

    if (applications.length === 0) {
        applicationsTable.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';

    applicationsTable.innerHTML = applications.map(app => `
        <tr data-id="${app.id}">
            <td>
                <div class="company-cell">
                    <div class="company-avatar">${app.company_name.charAt(0).toUpperCase()}</div>
                    <div class="company-info">
                        <span class="company-name">${escapeHtml(app.company_name)}</span>
                        ${app.job_url ? `<a href="${app.job_url}" target="_blank" class="company-url">View Job</a>` : ''}
                    </div>
                </div>
            </td>
            <td>${escapeHtml(app.position)}</td>
            <td>${app.location ? escapeHtml(app.location) : '-'}</td>
            <td><span class="status-badge ${app.status}">${formatStatus(app.status)}</span></td>
            <td class="date-cell">${app.applied_at ? formatDate(app.applied_at) : '-'}</td>
            <td class="date-cell ${isUpcoming(app.interview_at) ? 'upcoming' : ''}">${app.interview_at ? formatDate(app.interview_at) : '-'}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn view" onclick="viewApplication(${app.id})" title="View Details">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                    </button>
                    <button class="action-btn edit" onclick="editApplication(${app.id})" title="Edit">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                    </button>
                    <button class="action-btn delete" onclick="confirmDelete(${app.id})" title="Delete">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * Open modal for add/edit
 */
function openModal(application = null) {
    document.getElementById('modal-title').textContent = application ? 'Edit Application' : 'Add Application';

    if (application) {
        document.getElementById('application-id').value = application.id;
        document.getElementById('company-name').value = application.company_name || '';
        document.getElementById('position').value = application.position || '';
        document.getElementById('location').value = application.location || '';
        document.getElementById('salary-range').value = application.salary_range || '';
        document.getElementById('job-url').value = application.job_url || '';
        document.getElementById('status').value = application.status || 'saved';
        document.getElementById('deadline').value = application.deadline ? formatDateTimeLocal(application.deadline) : '';
        document.getElementById('interview-at').value = application.interview_at ? formatDateTimeLocal(application.interview_at) : '';
        document.getElementById('contact-email').value = application.contact_email || '';
        document.getElementById('notes').value = application.notes || '';
    } else {
        applicationForm.reset();
        document.getElementById('application-id').value = '';
    }

    applicationModal.style.display = 'flex';
}

/**
 * Close modal
 */
function closeModal() {
    applicationModal.style.display = 'none';
    applicationForm.reset();
}

/**
 * Handle form submit
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('application-id').value;
    const data = {
        company_name: document.getElementById('company-name').value,
        position: document.getElementById('position').value,
        location: document.getElementById('location').value || null,
        salary_range: document.getElementById('salary-range').value || null,
        job_url: document.getElementById('job-url').value || null,
        status: document.getElementById('status').value,
        deadline: document.getElementById('deadline').value || null,
        interview_at: document.getElementById('interview-at').value || null,
        contact_email: document.getElementById('contact-email').value || null,
        notes: document.getElementById('notes').value || null,
    };

    try {
        const url = id
            ? `${API_BASE_URL}/applications/${id}`
            : `${API_BASE_URL}/applications/`;

        const response = await fetch(url, {
            method: id ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail?.message || 'Failed to save application');
        }

        closeModal();
        loadApplications();
        loadStats();
    } catch (error) {
        console.error('Save error:', error);
        alert(error.message);
    }
}

/**
 * View application details
 */
async function viewApplication(id) {
    currentApplicationId = id;

    try {
        const response = await fetch(`${API_BASE_URL}/applications/${id}`);
        if (!response.ok) throw new Error('Failed to load application');

        const app = await response.json();

        document.getElementById('detail-title').textContent = `${app.company_name} - ${app.position}`;
        document.getElementById('detail-content').innerHTML = `
            <div class="detail-grid">
                <div class="detail-section">
                    <h4>Company</h4>
                    <p>${escapeHtml(app.company_name)}</p>
                </div>
                <div class="detail-section">
                    <h4>Position</h4>
                    <p>${escapeHtml(app.position)}</p>
                </div>
                <div class="detail-section">
                    <h4>Location</h4>
                    <p>${app.location || '-'}</p>
                </div>
                <div class="detail-section">
                    <h4>Salary Range</h4>
                    <p>${app.salary_range || '-'}</p>
                </div>
                <div class="detail-section">
                    <h4>Status</h4>
                    <p><span class="status-badge ${app.status}">${formatStatus(app.status)}</span></p>
                </div>
                <div class="detail-section">
                    <h4>Applied Date</h4>
                    <p>${app.applied_at ? formatDate(app.applied_at) : '-'}</p>
                </div>
                <div class="detail-section">
                    <h4>Interview Date</h4>
                    <p>${app.interview_at ? formatDate(app.interview_at) : '-'}</p>
                </div>
                <div class="detail-section">
                    <h4>Deadline</h4>
                    <p>${app.deadline ? formatDate(app.deadline) : '-'}</p>
                </div>
            </div>
            ${app.job_url ? `
                <div class="detail-section">
                    <h4>Job URL</h4>
                    <p><a href="${app.job_url}" target="_blank">${app.job_url}</a></p>
                </div>
            ` : ''}
            ${app.contact_email ? `
                <div class="detail-section">
                    <h4>Contact</h4>
                    <p>${app.contact_name || ''} ${app.contact_email ? `<a href="mailto:${app.contact_email}">${app.contact_email}</a>` : ''}</p>
                </div>
            ` : ''}
            ${app.notes ? `
                <div class="detail-section">
                    <h4>Notes</h4>
                    <p>${escapeHtml(app.notes)}</p>
                </div>
            ` : ''}
            ${app.activity_log && app.activity_log.length > 0 ? `
                <div class="activity-log">
                    <h4>Activity Log</h4>
                    ${app.activity_log.slice().reverse().map(log => `
                        <div class="activity-item">
                            <div class="activity-dot"></div>
                            <div class="activity-content">
                                <div class="activity-action">${escapeHtml(log.action)}</div>
                                <div class="activity-time">${formatDate(log.timestamp)}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        `;

        detailModal.style.display = 'flex';
    } catch (error) {
        console.error('View error:', error);
        alert('Failed to load application details');
    }
}

/**
 * Close detail modal
 */
function closeDetailModal() {
    detailModal.style.display = 'none';
    currentApplicationId = null;
}

/**
 * Edit application
 */
function editApplication(id) {
    const app = applications.find(a => a.id === id);
    if (app) openModal(app);
}

/**
 * Confirm delete
 */
function confirmDelete(id) {
    if (confirm('Are you sure you want to delete this application?')) {
        deleteApplication(id);
    }
}

/**
 * Delete application
 */
async function deleteApplication(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/applications/${id}`, {
            method: 'DELETE',
        });

        if (!response.ok) throw new Error('Failed to delete application');

        loadApplications();
        loadStats();
    } catch (error) {
        console.error('Delete error:', error);
        alert('Failed to delete application');
    }
}

/**
 * Show loading state
 */
function showLoading() {
    loadingState.style.display = 'block';
    emptyState.style.display = 'none';
}

/**
 * Hide loading state
 */
function hideLoading() {
    loadingState.style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    hideLoading();
    alert(message);
}

/**
 * Format status for display
 */
function formatStatus(status) {
    return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

/**
 * Format date for datetime-local input
 */
function formatDateTimeLocal(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toISOString().slice(0, 16);
}

/**
 * Check if date is upcoming (within 7 days)
 */
function isUpcoming(dateStr) {
    if (!dateStr) return false;
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date - now;
    return diff > 0 && diff < 7 * 24 * 60 * 60 * 1000;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
