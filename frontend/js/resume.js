/**
 * Resume Analysis UI Logic - PathPilot
 *
 * Constitution Compliance:
 * - T032: Frontend JavaScript with Fetch API
 * - User-friendly drag-and-drop upload
 * - Real-time analysis display
 */

// API Configuration
// WSL2 환경: localhost가 Windows를 가리키므로 WSL2 IP 사용
const API_BASE_URL = 'http://172.23.78.180:8000/api/v1';

// DOM Elements
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const browseBtn = document.getElementById('browse-btn');
const filePreview = document.getElementById('file-preview');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const removeFileBtn = document.getElementById('remove-file');
const uploadBtn = document.getElementById('upload-btn');
const loading = document.getElementById('loading');
const errorMessage = document.getElementById('error-message');
const errorText = document.getElementById('error-text');
const resultsSection = document.getElementById('results-section');
const analyzeAnotherBtn = document.getElementById('analyze-another');

// State
let selectedFile = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Browse button
    browseBtn.addEventListener('click', () => fileInput.click());

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Drag and drop
    dropzone.addEventListener('dragover', handleDragOver);
    dropzone.addEventListener('dragleave', handleDragLeave);
    dropzone.addEventListener('drop', handleDrop);

    // Remove file
    removeFileBtn.addEventListener('click', clearFileSelection);

    // Upload button
    uploadBtn.addEventListener('click', uploadResume);

    // Analyze another
    analyzeAnotherBtn.addEventListener('click', resetForm);
}

/**
 * Handle drag over event
 */
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add('drag-over');
}

/**
 * Handle drag leave event
 */
function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-over');
}

/**
 * Handle file drop
 */
function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

/**
 * Handle file selection
 */
function handleFileSelect(file) {
    // Validate file type (check both MIME type and extension)
    const validMimeTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',  // Legacy .doc
        'application/octet-stream',  // Sometimes returned for .docx
    ];
    const validExtensions = ['.pdf', '.docx', '.doc'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    const isValidType = validMimeTypes.includes(file.type) || validExtensions.includes(fileExtension);
    if (!isValidType) {
        showError(`Invalid file type (${file.type || 'unknown'}). Please upload a PDF or DOCX file.`);
        return;
    }

    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
    if (file.size > maxSize) {
        showError('File too large. Maximum size is 5MB.');
        return;
    }

    // Store selected file
    selectedFile = file;

    // Update UI
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);

    dropzone.style.display = 'none';
    filePreview.style.display = 'flex';
    uploadBtn.style.display = 'block';
    hideError();
}

/**
 * Clear file selection
 */
function clearFileSelection() {
    selectedFile = null;
    fileInput.value = '';

    dropzone.style.display = 'flex';
    filePreview.style.display = 'none';
    uploadBtn.style.display = 'none';
}

/**
 * Upload resume and get analysis
 */
async function uploadResume() {
    if (!selectedFile) {
        showError('Please select a file first.');
        return;
    }

    // Show loading state
    uploadBtn.style.display = 'none';
    loading.style.display = 'block';
    hideError();

    try {
        // Create form data
        const formData = new FormData();
        formData.append('file', selectedFile);

        // Upload file
        const response = await fetch(`${API_BASE_URL}/resume/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.message || 'Upload failed');
        }

        const data = await response.json();

        // Hide loading
        loading.style.display = 'none';

        // Display results
        displayResults(data.analysis);

    } catch (error) {
        console.error('Upload error:', error);
        loading.style.display = 'none';
        uploadBtn.style.display = 'block';
        showError(error.message || 'Failed to analyze resume. Please try again.');
    }
}

/**
 * Display analysis results
 */
function displayResults(analysis) {
    // Hide upload section
    document.querySelector('.upload-section').style.display = 'none';

    // Show results section
    resultsSection.style.display = 'block';

    // Populate experience years
    document.getElementById('experience-years').textContent = analysis.experience_years || 0;

    // Populate skills
    const skillsContainer = document.getElementById('skills-container');
    skillsContainer.innerHTML = '';
    if (analysis.skills && analysis.skills.length > 0) {
        analysis.skills.forEach(skill => {
            const skillBadge = document.createElement('span');
            skillBadge.className = 'skill-badge';
            skillBadge.textContent = skill;
            skillsContainer.appendChild(skillBadge);
        });
    } else {
        skillsContainer.innerHTML = '<p class="no-data">No skills identified</p>';
    }

    // Populate strengths
    populateList('strengths-list', analysis.strengths);

    // Populate weaknesses
    populateList('weaknesses-list', analysis.weaknesses);

    // Populate recommendations
    populateList('recommendations-list', analysis.recommendations);

    // Populate suitable roles
    populateList('suitable-roles-list', analysis.suitable_roles);

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Populate a list with items
 */
function populateList(listId, items) {
    const list = document.getElementById(listId);
    list.innerHTML = '';

    if (items && items.length > 0) {
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            list.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.className = 'no-data';
        li.textContent = 'No items to display';
        list.appendChild(li);
    }
}

/**
 * Reset form to initial state
 */
function resetForm() {
    clearFileSelection();
    resultsSection.style.display = 'none';
    document.querySelector('.upload-section').style.display = 'block';
    hideError();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Show error message
 */
function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'flex';
}

/**
 * Hide error message
 */
function hideError() {
    errorMessage.style.display = 'none';
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
