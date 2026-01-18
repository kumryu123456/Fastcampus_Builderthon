/**
 * Mock Interview UI Logic - PathPilot
 *
 * Constitution Compliance:
 * - T072-T076: Frontend JavaScript for mock interview feature
 * - User-friendly interview flow with AI evaluation
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// State
let currentInterview = null;
let currentQuestionIndex = 0;
let timerInterval = null;
let timeRemaining = 0;

// DOM Elements
const setupSection = document.getElementById('setup-section');
const loadingSection = document.getElementById('loading-section');
const interviewSection = document.getElementById('interview-section');
const evaluationSection = document.getElementById('evaluation-section');
const resultsSection = document.getElementById('results-section');
const historySection = document.getElementById('history-section');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadInterviewHistory();
    setupCharCounter();
});

// Character counter for answer textarea
function setupCharCounter() {
    const answerText = document.getElementById('answer-text');
    const charCount = document.getElementById('char-count');

    if (answerText && charCount) {
        answerText.addEventListener('input', () => {
            charCount.textContent = answerText.value.length;
        });
    }
}

// Start Interview
async function startInterview() {
    const jobTitle = document.getElementById('job-title').value.trim();
    const companyName = document.getElementById('company-name').value.trim();
    const jobDescription = document.getElementById('job-description').value.trim();
    const interviewType = document.getElementById('interview-type').value;
    const difficulty = document.getElementById('difficulty').value;
    const questionCount = parseInt(document.getElementById('question-count').value);
    const language = document.getElementById('language').value;

    // Validation
    if (!jobTitle) {
        alert('Please enter a job title.');
        return;
    }

    // Show loading
    showSection('loading');

    try {
        const response = await fetch(`${API_BASE_URL}/interview/generate-questions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                job_title: jobTitle,
                company_name: companyName || null,
                job_description: jobDescription || null,
                interview_type: interviewType,
                difficulty: difficulty,
                question_count: questionCount,
                language: language,
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to generate interview questions');
        }

        const data = await response.json();
        currentInterview = data;
        currentQuestionIndex = 0;

        // Start interview
        showSection('interview');
        displayQuestion();

    } catch (error) {
        console.error('Error starting interview:', error);
        alert('Failed to start interview. Please try again.');
        showSection('setup');
    }
}

// Display current question
function displayQuestion() {
    if (!currentInterview || !currentInterview.questions) return;

    const question = currentInterview.questions[currentQuestionIndex];
    const totalQuestions = currentInterview.questions.length;

    // Update progress
    const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100;
    document.getElementById('progress-fill').style.width = `${progress}%`;
    document.getElementById('progress-text').textContent =
        `Question ${currentQuestionIndex + 1} of ${totalQuestions}`;

    // Update question content
    document.getElementById('question-type').textContent = formatQuestionType(question.type);
    document.getElementById('question-difficulty').textContent = `Difficulty: ${question.difficulty}/5`;
    document.getElementById('question-text').textContent = question.question;

    const tipElement = document.getElementById('question-tip');
    if (question.tips) {
        tipElement.textContent = `Tip: ${question.tips}`;
        tipElement.style.display = 'block';
    } else {
        tipElement.style.display = 'none';
    }

    // Update expected topics
    const topicTags = document.getElementById('topic-tags');
    topicTags.innerHTML = question.expected_topics
        .map(topic => `<span class="topic-tag">${topic}</span>`)
        .join('');

    // Clear answer
    document.getElementById('answer-text').value = '';
    document.getElementById('char-count').textContent = '0';

    // Start timer
    startTimer(question.time_limit_seconds || 120);
}

// Format question type for display
function formatQuestionType(type) {
    const types = {
        'behavioral': 'Behavioral',
        'technical': 'Technical',
        'situational': 'Situational'
    };
    return types[type] || type;
}

// Timer functions
function startTimer(seconds) {
    clearInterval(timerInterval);
    timeRemaining = seconds;
    updateTimerDisplay();

    timerInterval = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();

        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            // Auto-submit or show warning
        }
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;

    const timerElement = document.getElementById('timer');
    const timerText = document.getElementById('timer-text');
    timerText.textContent = display;

    // Update timer style based on time remaining
    timerElement.classList.remove('warning', 'danger');
    if (timeRemaining <= 30) {
        timerElement.classList.add('danger');
    } else if (timeRemaining <= 60) {
        timerElement.classList.add('warning');
    }
}

function stopTimer() {
    clearInterval(timerInterval);
}

// Submit answer
async function submitAnswer() {
    const answerText = document.getElementById('answer-text').value.trim();

    if (!answerText) {
        alert('Please enter your answer before submitting.');
        return;
    }

    stopTimer();

    const question = currentInterview.questions[currentQuestionIndex];
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Evaluating...';

    try {
        const response = await fetch(
            `${API_BASE_URL}/interview/${currentInterview.interview_id}/evaluate-answer`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question_id: question.id,
                    answer_text: answerText,
                }),
            }
        );

        if (!response.ok) {
            throw new Error('Failed to evaluate answer');
        }

        const result = await response.json();
        displayEvaluation(result);

    } catch (error) {
        console.error('Error evaluating answer:', error);
        alert('Failed to evaluate answer. Please try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Answer';
    }
}

// Display evaluation result
function displayEvaluation(result) {
    const evaluation = result.evaluation;
    const score = evaluation.score;

    // Update score badge
    const scoreBadge = document.getElementById('score-badge');
    document.getElementById('score-value').textContent = score;

    scoreBadge.classList.remove('excellent', 'good', 'average', 'poor');
    if (score >= 85) scoreBadge.classList.add('excellent');
    else if (score >= 70) scoreBadge.classList.add('good');
    else if (score >= 50) scoreBadge.classList.add('average');
    else scoreBadge.classList.add('poor');

    // Update feedback
    document.getElementById('feedback-text').textContent = evaluation.feedback;

    // Update strengths
    const strengthsList = document.getElementById('strengths-list');
    strengthsList.innerHTML = evaluation.strengths
        .map(s => `<li>${s}</li>`)
        .join('');

    // Update improvements
    const improvementsList = document.getElementById('improvements-list');
    improvementsList.innerHTML = evaluation.improvements
        .map(i => `<li>${i}</li>`)
        .join('');

    // Update model answer
    document.getElementById('model-answer').innerHTML =
        `<p>${evaluation.model_answer || 'No model answer provided.'}</p>`;

    // Update next button
    const nextBtn = document.getElementById('next-btn');
    if (result.is_completed) {
        nextBtn.textContent = 'View Results';
        nextBtn.onclick = showResults;
    } else {
        nextBtn.textContent = 'Next Question';
        nextBtn.onclick = nextQuestion;
    }

    // Store result for final summary
    if (!currentInterview.results) {
        currentInterview.results = [];
    }
    currentInterview.results[currentQuestionIndex] = result;

    showSection('evaluation');
}

// Skip question
function skipQuestion() {
    if (confirm('Are you sure you want to skip this question? You can come back to it later.')) {
        stopTimer();

        // Store skip
        if (!currentInterview.results) {
            currentInterview.results = [];
        }
        currentInterview.results[currentQuestionIndex] = {
            evaluation: { score: 0, strengths: [], improvements: ['Question was skipped'] },
            skipped: true
        };

        nextQuestion();
    }
}

// Retry current question
function retryQuestion() {
    document.getElementById('submit-btn').disabled = false;
    document.getElementById('submit-btn').textContent = 'Submit Answer';
    showSection('interview');
    startTimer(currentInterview.questions[currentQuestionIndex].time_limit_seconds || 120);
}

// Go to next question
function nextQuestion() {
    currentQuestionIndex++;

    if (currentQuestionIndex >= currentInterview.questions.length) {
        showResults();
    } else {
        document.getElementById('submit-btn').disabled = false;
        document.getElementById('submit-btn').textContent = 'Submit Answer';
        showSection('interview');
        displayQuestion();
    }
}

// Show results
async function showResults() {
    // Calculate statistics
    const results = currentInterview.results || [];
    const scores = results
        .filter(r => r && r.evaluation && !r.skipped)
        .map(r => r.evaluation.score);

    const questionsAnswered = scores.length;
    const avgScore = scores.length > 0
        ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
        : 0;
    const bestScore = scores.length > 0 ? Math.max(...scores) : 0;

    // Update final score display
    document.querySelector('.final-score-value').textContent = avgScore;
    document.getElementById('questions-answered').textContent = questionsAnswered;
    document.getElementById('avg-score').textContent = avgScore;
    document.getElementById('best-score').textContent = bestScore;

    // Display question breakdown
    const questionScores = document.getElementById('question-scores');
    questionScores.innerHTML = currentInterview.questions
        .map((q, i) => {
            const result = results[i];
            const score = result && result.evaluation ? result.evaluation.score : 0;
            const skipped = result && result.skipped;
            const scoreClass = getScoreClass(score);

            return `
                <div class="question-score-item">
                    <span class="question-num">Q${i + 1}: ${q.question.substring(0, 50)}...</span>
                    <span class="question-score ${scoreClass}">
                        ${skipped ? 'Skipped' : score + '/100'}
                    </span>
                </div>
            `;
        })
        .join('');

    showSection('results');

    // Refresh history
    await loadInterviewHistory();
}

// Get score class for styling
function getScoreClass(score) {
    if (score >= 85) return 'excellent';
    if (score >= 70) return 'good';
    if (score >= 50) return 'average';
    return 'poor';
}

// Review answers
function reviewAnswers() {
    // TODO: Implement review mode
    alert('Review feature coming soon!');
}

// Start new interview
function newInterview() {
    currentInterview = null;
    currentQuestionIndex = 0;

    // Reset form
    document.getElementById('job-title').value = '';
    document.getElementById('company-name').value = '';
    document.getElementById('job-description').value = '';

    showSection('setup');
}

// Load interview history
async function loadInterviewHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/interview/?limit=5`);

        if (!response.ok) {
            throw new Error('Failed to load history');
        }

        const data = await response.json();
        displayHistory(data.interviews);

    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Display interview history
function displayHistory(interviews) {
    const historyList = document.getElementById('history-list');

    if (!interviews || interviews.length === 0) {
        historyList.innerHTML = '<p class="no-history">No interview history yet. Start your first mock interview above!</p>';
        return;
    }

    historyList.innerHTML = interviews.map(interview => {
        const score = interview.total_score || 0;
        const scoreClass = getScoreClass(score);
        const date = new Date(interview.created_at).toLocaleDateString('ko-KR');

        return `
            <div class="history-item" onclick="loadInterview(${interview.id})">
                <div class="history-info">
                    <div class="history-title">${interview.job_title}</div>
                    <div class="history-meta">
                        ${interview.company_name || 'Unknown Company'} |
                        ${interview.question_count} questions |
                        ${date}
                    </div>
                </div>
                <div class="history-score ${scoreClass}">${Math.round(score)}</div>
            </div>
        `;
    }).join('');
}

// Load a past interview
async function loadInterview(interviewId) {
    try {
        const response = await fetch(`${API_BASE_URL}/interview/${interviewId}`);

        if (!response.ok) {
            throw new Error('Failed to load interview');
        }

        const data = await response.json();

        // Display the past interview results
        currentInterview = {
            interview_id: data.interview_id,
            questions: data.questions,
            results: data.answers.map(a => ({
                evaluation: a.evaluation
            }))
        };

        showResults();

    } catch (error) {
        console.error('Error loading interview:', error);
        alert('Failed to load interview.');
    }
}

// Section visibility
function showSection(sectionName) {
    setupSection.classList.add('hidden');
    loadingSection.classList.add('hidden');
    interviewSection.classList.add('hidden');
    evaluationSection.classList.add('hidden');
    resultsSection.classList.add('hidden');

    switch (sectionName) {
        case 'setup':
            setupSection.classList.remove('hidden');
            historySection.classList.remove('hidden');
            break;
        case 'loading':
            loadingSection.classList.remove('hidden');
            historySection.classList.add('hidden');
            break;
        case 'interview':
            interviewSection.classList.remove('hidden');
            historySection.classList.add('hidden');
            break;
        case 'evaluation':
            evaluationSection.classList.remove('hidden');
            historySection.classList.add('hidden');
            break;
        case 'results':
            resultsSection.classList.remove('hidden');
            historySection.classList.remove('hidden');
            break;
    }
}
