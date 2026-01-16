# Feature Specification: PathPilot Job Application Automation

**Feature Branch**: `001-pathpilot-mvp`
**Created**: 2025-01-16
**Status**: Draft
**Input**: PathPilot automates the job application process with AI-powered resume analysis, job discovery, cover letter generation, mock interviews, and application tracking.

## User Scenarios & Testing

### User Story 1 - Resume Upload & Analysis (Priority: P1) 🎯 MVP

User uploads their resume and receives immediate AI-powered analysis of strengths, weaknesses, and optimization recommendations.

**Why this priority**: Core value proposition - users need resume insights before any other feature makes sense. This is the entry point to the entire system and the foundation for personalization.

**Independent Test**: User can upload a PDF/DOCX resume, receive structured analysis within 60 seconds, and view detailed feedback without requiring any other features to be implemented.

**Acceptance Scenarios**:

1. **Given** user is on the dashboard, **When** they upload a resume file (PDF or DOCX), **Then** system extracts text, sends to Claude API, and displays analysis with strengths/weaknesses sections
2. **Given** resume upload is in progress, **When** Claude API call fails, **Then** system retries with exponential backoff (3 attempts) and shows error message if all retries fail
3. **Given** user has uploaded resume, **When** analysis completes, **Then** results are persisted to database and retrievable on subsequent visits
4. **Given** user uploads invalid file type, **When** validation runs, **Then** system rejects upload and shows clear error message

---

### User Story 2 - Cover Letter Generation (Priority: P1) 🎯 MVP

User selects a job posting and receives AI-generated personalized cover letter based on their resume analysis.

**Why this priority**: Immediate value delivery - this is what users will demo. Combines resume analysis (US1) with generative AI to solve a real pain point.

**Independent Test**: Given a resume analysis exists, user can input job description, click "Generate Cover Letter", and receive personalized output in <60 seconds without requiring job discovery or other features.

**Acceptance Scenarios**:

1. **Given** user has analyzed resume, **When** they paste job description and click "Generate Cover Letter", **Then** Claude generates personalized letter matching resume strengths to job requirements in <60 seconds
2. **Given** cover letter generation is triggered, **When** Claude API call times out, **Then** system retries with exponential backoff and provides status updates to user
3. **Given** generated cover letter is displayed, **When** user clicks "Edit", **Then** they can modify content and save customized version
4. **Given** user generates cover letter, **When** they click "Save", **Then** letter is associated with job posting and stored in application tracking system

---

### User Story 3 - Job Discovery Agent (Priority: P2)

User sets job search criteria (title, location, experience level) and autonomous AI agent discovers matching postings daily using LangGraph workflow.

**Why this priority**: Automation value - reduces manual job hunting. Requires more complex agentic architecture (LangGraph) so deferred until core features work.

**Independent Test**: User can configure search criteria, trigger agent, and receive list of matching jobs from external APIs without requiring cover letter generation or interviews to function.

**Acceptance Scenarios**:

1. **Given** user sets criteria (job title="Software Engineer", location="Remote", experience="Mid-level"), **When** they activate job discovery agent, **Then** LangGraph workflow searches job boards and returns 10+ matching postings
2. **Given** job discovery agent is running, **When** external job API fails, **Then** circuit breaker activates, agent gracefully degrades and logs failure with structured context
3. **Given** agent finds new jobs, **When** daily scan completes, **Then** user receives notification with count of new matches and dashboard updates
4. **Given** user views discovered jobs, **When** they click "Generate Cover Letter", **Then** job description auto-populates in cover letter generator (integrates with US2)

---

### User Story 4 - Mock Interview Practice (Priority: P2)

User practices interview with AI interviewer powered by Claude (questions) and ElevenLabs (voice synthesis) with <2 second response latency.

**Why this priority**: High demo appeal but requires ElevenLabs integration and real-time performance optimization. Not critical for MVP launch.

**Independent Test**: User can start interview session, speak/type answers, receive AI follow-up questions with voice playback, and review session transcript independently of other features.

**Acceptance Scenarios**:

1. **Given** user clicks "Start Mock Interview", **When** session begins, **Then** AI asks first question using ElevenLabs voice synthesis with <2 second latency
2. **Given** user provides answer, **When** they submit, **Then** Claude analyzes response and generates contextual follow-up question within 2 seconds
3. **Given** interview session in progress, **When** ElevenLabs API fails, **Then** system falls back to text-only mode and continues interview without voice
4. **Given** interview completes, **When** user views results, **Then** system shows transcript, performance analysis, and improvement recommendations

---

### User Story 5 - Application Dashboard (Priority: P3)

User views all job applications in one place with timeline visualization, application status, and success statistics.

**Why this priority**: Nice-to-have polish - improves UX but not essential for core demo. Deferred until P1/P2 features are complete.

**Independent Test**: User can view dashboard showing all saved cover letters, job applications, and mock interview sessions with filtering and search capability.

**Acceptance Scenarios**:

1. **Given** user has generated 5 cover letters, **When** they open dashboard, **Then** all applications display with job title, company, date, and status
2. **Given** user views dashboard timeline, **When** they filter by date range, **Then** applications update to show only matching entries
3. **Given** user has completed 3 mock interviews, **When** they view stats panel, **Then** system shows total interviews, average score, and improvement trends

---

### Edge Cases

- **Resume parsing failures**: What happens when PDF has non-standard formatting or is image-based?
- **Claude API rate limits**: How does system handle quota exhaustion during high traffic?
- **Concurrent cover letter generation**: Can system handle 100 users generating letters simultaneously?
- **ElevenLabs voice synthesis delays**: What if latency exceeds 2 seconds during network congestion?
- **Job API schema changes**: How does agent adapt when external job boards change their response format?
- **Resume PII scrubbing**: How do we prevent sensitive data (SSN, references) from being logged?

## Requirements

### Functional Requirements

- **FR-001**: System MUST accept resume uploads in PDF and DOCX formats (max 5MB file size)
- **FR-002**: System MUST extract text from resume using PyPDF2/python-docx libraries
- **FR-003**: System MUST send resume text to Claude API with prompt requesting structured analysis (strengths, weaknesses, recommendations)
- **FR-004**: System MUST implement retry logic for Claude API calls with 3 attempts, exponential backoff (1s, 2s, 4s), and clear timeout (30s per request)
- **FR-005**: System MUST implement retry logic for ElevenLabs API calls with 3 attempts, exponential backoff, and graceful degradation to text-only mode
- **FR-006**: System MUST generate personalized cover letters in <60 seconds (95th percentile)
- **FR-007**: System MUST support mock interview with <2 second response time between user answer and next AI question
- **FR-008**: System MUST persist resume analysis, cover letters, and interview transcripts to database with user association
- **FR-009**: System MUST store API keys for Claude and ElevenLabs in environment variables only (never in code or logs)
- **FR-010**: System MUST scrub PII (Social Security Numbers, phone numbers, addresses) from logs and error messages
- **FR-011**: System MUST implement LangGraph workflow for autonomous job discovery agent with state persistence
- **FR-012**: System MUST implement circuit breaker pattern for external job board APIs (open after 5 consecutive failures)
- **FR-013**: System MUST support 100 concurrent users during demo (target load)
- **FR-014**: System MUST maintain 95% uptime during hackathon demo period
- **FR-015**: System MUST implement structured logging with log levels (DEBUG, INFO, WARNING, ERROR) and context (request_id, user_id, operation_name)

### Key Entities

- **User**: Represents job seeker, has unique ID, email, created_at timestamp
- **Resume**: Uploaded document, has file_path, original_filename, upload_date, analysis_result (JSON), associated with User
- **JobPosting**: Discovered or user-provided job, has title, company, description, location, job_url, source (manual/agent), discovered_date
- **CoverLetter**: Generated letter, has job_posting_id, resume_id, generated_content, user_edits, status (draft/final), created_at
- **MockInterview**: Interview session, has transcript (JSON array of Q&A), performance_score, feedback, duration_seconds, created_at
- **SearchCriteria**: User-defined job search parameters, has job_titles (array), locations (array), experience_level, active (boolean)

## Success Criteria

### Measurable Outcomes

- **SC-001**: Cover letter generation completes in <60 seconds for 95% of requests (measured via structured logs)
- **SC-002**: Mock interview response latency <2 seconds for 90% of interactions (measured via performance monitoring)
- **SC-003**: System handles 100 concurrent users with <5% error rate (measured during load testing)
- **SC-004**: 95% uptime during 48-hour hackathon demo window (measured via health check endpoint)
- **SC-005**: Zero credential leaks or PII exposure in logs during security audit (measured via pre-commit credential scanning)
- **SC-006**: Resume analysis accuracy validated by 5 test users rating quality ≥4/5 stars
- **SC-007**: All external API calls have retry logic verified through integration tests (100% coverage of API wrapper functions)
- **SC-008**: Test coverage meets 80% minimum threshold across all modules (measured via pytest-cov)

### Demo Story

**On-stage narrative for hackathon judges:**

1. "Meet Sarah, a software engineer looking for her next role. She uploads her resume to PathPilot..."
2. [Show resume upload] "Within seconds, our Claude-powered AI analyzes her background, highlighting her strengths in Python and distributed systems."
3. "Sarah finds a job posting for Senior Backend Engineer. With one click..." [Show cover letter generation]
4. "PathPilot generates a personalized cover letter that connects her experience to the role requirements in under 60 seconds."
5. "Before applying, Sarah wants to practice. She starts a mock interview..." [Show AI asking first question with voice]
6. "Our AI interviewer, powered by ElevenLabs voice synthesis, conducts a realistic technical interview and provides instant feedback."
7. [Show dashboard] "Sarah can track all her applications in one place, seeing exactly where she stands in her job search."

**Key demo metrics to highlight:**
- Cover letter generation speed (<60s)
- Voice interview responsiveness (<2s)
- Number of jobs discovered by autonomous agent
- Resume analysis depth (strengths/weaknesses/recommendations)
