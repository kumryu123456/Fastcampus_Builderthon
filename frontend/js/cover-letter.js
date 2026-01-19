/**
 * Cover Letter Generator UI Logic - PathPilot
 *
 * Constitution Compliance:
 * - T045-T048: Frontend JavaScript for cover letter feature
 * - User-friendly form with AI generation
 * - API_BASE_URL is defined in config.js
 */

// DOM Elements
const generationSection = document.getElementById('generation-section');
const resultsSection = document.getElementById('results-section');
const generateBtn = document.getElementById('generate-btn');
const loading = document.getElementById('loading');
const errorMessage = document.getElementById('error-message');
const errorText = document.getElementById('error-text');

// Form fields
const jobTitleInput = document.getElementById('job-title');
const companyNameInput = document.getElementById('company-name');
const jobDescriptionInput = document.getElementById('job-description');
const resumeSelect = document.getElementById('resume-select');
const toneSelect = document.getElementById('tone-select');
const lengthSelect = document.getElementById('length-select');
const focusAreasInput = document.getElementById('focus-areas');
const customInstructionsInput = document.getElementById('custom-instructions');

// Result elements
const resultJobTitle = document.getElementById('result-job-title');
const resultCompanyName = document.getElementById('result-company-name');
const wordCountSpan = document.getElementById('word-count');
const versionSpan = document.getElementById('version');
const coverLetterText = document.getElementById('cover-letter-text');
const contentDisplay = document.getElementById('content-display');
const contentEdit = document.getElementById('content-edit');
const editTextarea = document.getElementById('edit-textarea');

// Buttons
const copyBtn = document.getElementById('copy-btn');
const regenerateBtn = document.getElementById('regenerate-btn');
const editBtn = document.getElementById('edit-btn');
const saveEditBtn = document.getElementById('save-edit-btn');
const cancelEditBtn = document.getElementById('cancel-edit-btn');
const newLetterBtn = document.getElementById('new-letter-btn');

// State
let currentCoverLetterId = null;
let isEditing = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadUserResumes();
});

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    generateBtn.addEventListener('click', generateCoverLetter);
    copyBtn.addEventListener('click', copyToClipboard);
    regenerateBtn.addEventListener('click', regenerateCoverLetter);
    editBtn.addEventListener('click', enableEditMode);
    saveEditBtn.addEventListener('click', saveEdit);
    cancelEditBtn.addEventListener('click', cancelEdit);
    newLetterBtn.addEventListener('click', resetForm);
}

/**
 * Load user's analyzed resumes for selection
 */
async function loadUserResumes() {
    try {
        // For MVP, we'll fetch resumes from the API
        // This would be implemented when we have a list resumes endpoint
        // For now, we'll leave the select with just the default option
        console.log('Resume loading ready for integration');
    } catch (error) {
        console.error('Error loading resumes:', error);
    }
}

/**
 * Generate cover letter
 */
async function generateCoverLetter() {
    // Validate required fields
    const jobTitle = jobTitleInput.value.trim();
    const companyName = companyNameInput.value.trim();

    if (!jobTitle) {
        showError('Please enter a job title.');
        jobTitleInput.focus();
        return;
    }

    if (!companyName) {
        showError('Please enter a company name.');
        companyNameInput.focus();
        return;
    }

    // Show loading state
    generateBtn.style.display = 'none';
    loading.style.display = 'block';
    hideError();

    try {
        // Parse focus areas
        const focusAreas = focusAreasInput.value.trim()
            ? focusAreasInput.value.split(',').map(s => s.trim()).filter(Boolean)
            : null;

        // Build request body
        const requestBody = {
            job_title: jobTitle,
            company_name: companyName,
            job_description: jobDescriptionInput.value.trim() || null,
            resume_id: resumeSelect.value ? parseInt(resumeSelect.value) : null,
            tone: toneSelect.value,
            length: lengthSelect.value,
            focus_areas: focusAreas,
            custom_instructions: customInstructionsInput.value.trim() || null,
        };

        // Call API
        const response = await fetch(`${API_BASE_URL}/cover-letter/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.message || 'Generation failed');
        }

        const data = await response.json();

        // Hide loading
        loading.style.display = 'none';

        // Store current cover letter ID
        currentCoverLetterId = data.cover_letter_id;

        // Display results
        displayResults(data);

    } catch (error) {
        console.error('Generation error:', error);
        loading.style.display = 'none';
        generateBtn.style.display = 'block';
        showError(error.message || 'Failed to generate cover letter. Please try again.');
    }
}

/**
 * Display generation results
 */
function displayResults(data) {
    // Hide generation section, show results
    generationSection.style.display = 'none';
    resultsSection.style.display = 'block';

    // Update header
    resultJobTitle.textContent = data.job_title;
    resultCompanyName.textContent = `at ${data.company_name}`;

    // Update meta
    wordCountSpan.textContent = data.word_count;
    versionSpan.textContent = data.version;

    // Update content
    coverLetterText.textContent = data.content;

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Copy cover letter to clipboard
 */
async function copyToClipboard() {
    try {
        await navigator.clipboard.writeText(coverLetterText.textContent);
        showToast('Copied to clipboard!');
    } catch (error) {
        console.error('Copy failed:', error);
        showError('Failed to copy. Please select and copy manually.');
    }
}

/**
 * Regenerate cover letter
 */
async function regenerateCoverLetter() {
    if (!currentCoverLetterId) return;

    regenerateBtn.disabled = true;
    regenerateBtn.textContent = 'Regenerating...';

    try {
        const response = await fetch(`${API_BASE_URL}/cover-letter/${currentCoverLetterId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ regenerate: true }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.message || 'Regeneration failed');
        }

        const data = await response.json();

        // Update display
        coverLetterText.textContent = data.content;
        wordCountSpan.textContent = data.word_count;
        versionSpan.textContent = data.version;

        showToast('Cover letter regenerated!');

    } catch (error) {
        console.error('Regeneration error:', error);
        showError(error.message);
    } finally {
        regenerateBtn.disabled = false;
        regenerateBtn.textContent = 'Regenerate';
    }
}

/**
 * Enable edit mode
 */
function enableEditMode() {
    isEditing = true;
    editTextarea.value = coverLetterText.textContent;
    contentDisplay.style.display = 'none';
    contentEdit.style.display = 'block';
    editTextarea.focus();
}

/**
 * Save edited content
 */
async function saveEdit() {
    if (!currentCoverLetterId) return;

    const newContent = editTextarea.value.trim();
    if (!newContent) {
        showError('Content cannot be empty.');
        return;
    }

    saveEditBtn.disabled = true;
    saveEditBtn.textContent = 'Saving...';

    try {
        const response = await fetch(`${API_BASE_URL}/cover-letter/${currentCoverLetterId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: newContent }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.message || 'Save failed');
        }

        const data = await response.json();

        // Update display
        coverLetterText.textContent = data.content;
        wordCountSpan.textContent = data.word_count;
        versionSpan.textContent = data.version;

        // Exit edit mode
        cancelEdit();
        showToast('Changes saved!');

    } catch (error) {
        console.error('Save error:', error);
        showError(error.message);
    } finally {
        saveEditBtn.disabled = false;
        saveEditBtn.textContent = 'Save Changes';
    }
}

/**
 * Cancel edit mode
 */
function cancelEdit() {
    isEditing = false;
    contentDisplay.style.display = 'block';
    contentEdit.style.display = 'none';
}

/**
 * Reset form to create new cover letter
 */
function resetForm() {
    // Reset state
    currentCoverLetterId = null;
    isEditing = false;

    // Show generation section, hide results
    generationSection.style.display = 'block';
    resultsSection.style.display = 'none';

    // Reset form fields
    jobTitleInput.value = '';
    companyNameInput.value = '';
    jobDescriptionInput.value = '';
    resumeSelect.value = '';
    toneSelect.value = 'professional';
    lengthSelect.value = 'medium';
    focusAreasInput.value = '';
    customInstructionsInput.value = '';

    // Reset UI
    generateBtn.style.display = 'block';
    loading.style.display = 'none';
    cancelEdit();
    hideError();

    // Scroll to top
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
 * Show toast notification
 */
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}
