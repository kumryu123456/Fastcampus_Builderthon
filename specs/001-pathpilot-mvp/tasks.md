# Tasks: PathPilot Job Application Automation

**Input**: Design documents from `/specs/001-pathpilot-mvp/`
**Prerequisites**: plan.md (completed), spec.md (completed), constitution.md

**Tests**: Tests are MANDATORY per Constitution Principle V (Code Quality). All test tasks must be completed.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. P1 stories (Resume Analysis + Cover Letter Generation) are CRITICAL for MVP demo.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Constitution requires: retry logic, PII scrubbing, structured logging, 80% test coverage

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend project structure per plan.md (backend/src/, backend/tests/, backend/requirements.txt)
- [ ] T002 Create frontend project structure per plan.md (frontend/src/, frontend/src/js/, frontend/src/css/)
- [ ] T003 [P] Initialize Python 3.11+ project with FastAPI, SQLAlchemy, pytest in backend/requirements.txt
- [ ] T004 [P] Create .env.example with ANTHROPIC_API_KEY, ELEVENLABS_API_KEY, DATABASE_URL in project root
- [ ] T005 [P] Create docker-compose.yml with PostgreSQL 15+ and backend service definitions
- [ ] T006 [P] Create .pre-commit-config.yaml with detect-secrets hook (Constitution III: User Privacy)

**Checkpoint**: Project structure ready - foundational work can begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create database schema in backend/src/database.py (SQLAlchemy setup, engine, sessionmaker)
- [ ] T008 [P] Implement retry logic decorator in backend/src/api/retry_wrapper.py with @retry_with_backoff(attempts=3, backoff=[1, 2, 4], timeout=30) (Constitution II: API Resilience)
- [ ] T009 [P] Implement circuit breaker pattern in backend/src/api/circuit_breaker.py for external APIs (Constitution II: API Resilience)
- [ ] T010 [P] Implement PII scrubbing utility in backend/src/utils/privacy.py with regex for SSN, phone, email (Constitution III: User Privacy)
- [ ] T011 [P] Setup structured logging in backend/src/utils/logging_config.py using structlog with request_id, user_id, operation, duration_ms fields (Constitution V: Code Quality)
- [ ] T012 [P] Create config loader in backend/src/config.py using python-dotenv for environment variables (Constitution III: User Privacy)
- [ ] T013 [P] Create base User model in backend/src/models/user.py (SQLAlchemy ORM: id, email, created_at)
- [ ] T014 Create FastAPI app in backend/src/main.py with CORS, logging middleware, health check endpoint
- [ ] T015 [P] Setup pytest configuration in backend/pytest.ini with coverage settings (80% threshold)
- [ ] T016 [P] Create pytest fixtures in backend/tests/conftest.py (test database, test client, mock API responses)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Resume Upload & Analysis (Priority: P1) 🎯 MVP

**Goal**: User uploads resume (PDF/DOCX), receives Claude-powered analysis with strengths/weaknesses in <60 seconds

**Independent Test**: Upload resume file → Extract text → Send to Claude API with retry logic → Display analysis → Persist to database

### Tests for User Story 1 (MANDATORY - Constitution V) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T017 [P] [US1] Contract test for POST /resume/upload in backend/tests/integration/test_resume_api.py (test successful upload, file validation, 5MB limit)
- [ ] T018 [P] [US1] Contract test for GET /resume/{id}/analysis in backend/tests/integration/test_resume_api.py (test analysis retrieval, 404 handling)
- [ ] T019 [P] [US1] Unit test for resume text extraction in backend/tests/unit/test_resume_service.py (test PDF extraction with PyPDF2, DOCX extraction with python-docx)
- [ ] T020 [P] [US1] Unit test for Claude API retry logic in backend/tests/unit/test_claude_client.py (test 3 retries, exponential backoff, timeout handling)
- [ ] T021 [P] [US1] Integration test for resume analysis workflow in backend/tests/integration/test_resume_workflow.py (test end-to-end: upload → extract → Claude call → persist)

### Implementation for User Story 1

- [ ] T022 [P] [US1] Create Resume model in backend/src/models/resume.py (SQLAlchemy ORM: id, user_id, file_path, original_filename, upload_date, analysis_result JSONB)
- [ ] T023 [P] [US1] Implement Claude API client in backend/src/api/claude_client.py with @retry_with_backoff decorator (Constitution II)
- [ ] T024 [US1] Implement file upload handler in backend/src/utils/file_handler.py (save with UUID filename, validate type/size, return secure path)
- [ ] T025 [US1] Implement text extraction service in backend/src/services/resume_service.py (extract_text_from_pdf using PyPDF2, extract_text_from_docx using python-docx)
- [ ] T026 [US1] Implement Claude resume analysis in backend/src/services/resume_service.py (analyze_resume function with prompt: "Analyze this resume and provide strengths, weaknesses, recommendations as JSON")
- [ ] T027 [US1] Create POST /resume/upload endpoint in backend/src/routers/resume.py (accept multipart/form-data, validate file, call resume_service, return analysis_id)
- [ ] T028 [US1] Create GET /resume/{id}/analysis endpoint in backend/src/routers/resume.py (retrieve analysis from database, return JSON response)
- [ ] T029 [US1] Add structured logging to resume service (log upload_started, extraction_completed, claude_api_called, analysis_persisted with request_id)
- [ ] T030 [US1] Add PII scrubbing to resume analysis logs (scrub SSN, phone, email from error messages using privacy.py utility)
- [ ] T031 [US1] Create frontend resume.html in frontend/src/resume.html (file upload form, drag-and-drop support, progress indicator)
- [ ] T032 [US1] Create frontend resume.js in frontend/src/js/resume.js (handle file upload, call POST /resume/upload, display analysis results with strengths/weaknesses sections)
- [ ] T033 [US1] Add CSS styling for resume page in frontend/src/css/styles.css (upload area, analysis display, error messages)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. User can upload resume and see AI analysis.

---

## Phase 4: User Story 2 - Cover Letter Generation (Priority: P1) 🎯 MVP

**Goal**: User pastes job description, receives personalized cover letter in <60 seconds based on resume analysis

**Independent Test**: Given resume analysis exists → User inputs job description → Claude generates cover letter → User can edit/save

### Tests for User Story 2 (MANDATORY - Constitution V) ⚠️

- [ ] T034 [P] [US2] Contract test for POST /cover-letter/generate in backend/tests/integration/test_cover_letter_api.py (test successful generation, <60s latency, retry logic)
- [ ] T035 [P] [US2] Contract test for PUT /cover-letter/{id}/edit in backend/tests/integration/test_cover_letter_api.py (test user edits, save functionality)
- [ ] T036 [P] [US2] Unit test for cover letter generation in backend/tests/unit/test_cover_letter_service.py (test prompt construction, Claude API call with resume + job description)
- [ ] T037 [P] [US2] Integration test for cover letter workflow in backend/tests/integration/test_cover_letter_workflow.py (test end-to-end: generate → display → edit → save)

### Implementation for User Story 2

- [ ] T038 [P] [US2] Create JobPosting model in backend/src/models/job_posting.py (SQLAlchemy ORM: id, user_id, title, company, description, location, job_url, source, discovered_date)
- [ ] T039 [P] [US2] Create CoverLetter model in backend/src/models/cover_letter.py (SQLAlchemy ORM: id, user_id, job_posting_id, resume_id, generated_content TEXT, user_edits TEXT, status, created_at)
- [ ] T040 [US2] Implement cover letter generation in backend/src/services/cover_letter_service.py (generate_cover_letter function: fetch resume analysis, combine with job description, send to Claude with prompt)
- [ ] T041 [US2] Create POST /cover-letter/generate endpoint in backend/src/routers/cover_letter.py (accept resume_id + job_description, call cover_letter_service, return letter_id + content)
- [ ] T042 [US2] Create PUT /cover-letter/{id}/edit endpoint in backend/src/routers/cover_letter.py (accept edited content, update user_edits field, return success)
- [ ] T043 [US2] Create GET /cover-letter/{id} endpoint in backend/src/routers/cover_letter.py (retrieve cover letter by ID, return content + metadata)
- [ ] T044 [US2] Add structured logging to cover letter service (log generation_started, claude_api_called, generation_completed with duration_ms, request_id)
- [ ] T045 [US2] Add performance monitoring to cover letter generation (track p95 latency, log warning if >60s, measure via structured logs)
- [ ] T046 [US2] Create frontend cover-letter.html in frontend/src/cover-letter.html (job description textarea, generate button, editable letter display, save button)
- [ ] T047 [US2] Create frontend cover-letter.js in frontend/src/js/cover-letter.js (handle generate request, show loading spinner, display letter, enable editing, save changes)
- [ ] T048 [US2] Add CSS styling for cover letter page in frontend/src/css/styles.css (job input area, letter display with formatting, edit/save buttons)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. MVP demo story is complete: upload resume → analyze → generate cover letter.

---

## Phase 5: User Story 3 - Job Discovery Agent (Priority: P2)

**Goal**: User sets search criteria, LangGraph autonomous agent discovers matching jobs daily from job boards

**Independent Test**: User configures criteria → Agent runs search → Returns 10+ matching jobs → User can generate cover letter for any job

### Tests for User Story 3 (MANDATORY - Constitution V) ⚠️

- [ ] T049 [P] [US3] Contract test for POST /jobs/search in backend/tests/integration/test_jobs_api.py (test search criteria submission, agent activation)
- [ ] T050 [P] [US3] Contract test for GET /jobs in backend/tests/integration/test_jobs_api.py (test job listing retrieval, pagination)
- [ ] T051 [P] [US3] Unit test for LangGraph workflow in backend/tests/unit/test_job_discovery_agent.py (test StateGraph nodes: search, filter, rank)
- [ ] T052 [P] [US3] Unit test for circuit breaker in backend/tests/unit/test_circuit_breaker.py (test opens after 5 failures, half-open state, recovery)
- [ ] T053 [P] [US3] Integration test for job discovery workflow in backend/tests/integration/test_job_discovery_workflow.py (test end-to-end: criteria → agent search → results persisted)

### Implementation for User Story 3

- [ ] T054 [P] [US3] Create SearchCriteria model in backend/src/models/search_criteria.py (SQLAlchemy ORM: id, user_id, job_titles JSON, locations JSON, experience_level, active)
- [ ] T055 [US3] Implement LangGraph job discovery agent in backend/src/services/job_discovery_agent.py (StateGraph with nodes: search_job_boards, filter_results, rank_by_relevance, persist_jobs)
- [ ] T056 [US3] Implement external job board API wrapper in backend/src/api/job_board_client.py (example: Indeed/LinkedIn API with circuit breaker pattern)
- [ ] T057 [US3] Create POST /jobs/search endpoint in backend/src/routers/jobs.py (accept search criteria, activate LangGraph agent, return job_count)
- [ ] T058 [US3] Create GET /jobs endpoint in backend/src/routers/jobs.py (retrieve discovered jobs for user, support pagination, return job list)
- [ ] T059 [US3] Add structured logging to job discovery agent (log agent_started, search_node_executed, jobs_found, agent_completed with structured context)
- [ ] T060 [US3] Add circuit breaker monitoring (log circuit_opened, circuit_half_open, circuit_closed events with failure counts)
- [ ] T061 [US3] Create frontend jobs.html in frontend/src/jobs.html (search criteria form, discovered jobs list, "Generate Cover Letter" buttons)
- [ ] T062 [US3] Create frontend jobs.js in frontend/src/js/jobs.js (handle search submission, display job results, integrate with cover letter generator)
- [ ] T063 [US3] Add integration between jobs and cover letters (clicking "Generate Cover Letter" on job auto-populates job description in cover-letter.html)

**Checkpoint**: Job discovery agent functional. User can configure search, agent finds jobs autonomously, user can generate cover letters for discovered jobs.

---

## Phase 6: User Story 4 - Mock Interview Practice (Priority: P2)

**Goal**: User practices interview with AI interviewer (Claude questions + ElevenLabs voice) with <2s response latency

**Independent Test**: User starts interview → AI asks question with voice → User answers → AI generates follow-up in <2s → Session transcript saved

### Tests for User Story 4 (MANDATORY - Constitution V) ⚠️

- [ ] T064 [P] [US4] Contract test for POST /interview/start in backend/tests/integration/test_interview_api.py (test session creation, first question generation)
- [ ] T065 [P] [US4] Contract test for POST /interview/answer in backend/tests/integration/test_interview_api.py (test answer submission, next question generation, <2s latency)
- [ ] T066 [P] [US4] Contract test for GET /interview/{id}/transcript in backend/tests/integration/test_interview_api.py (test transcript retrieval, performance analysis)
- [ ] T067 [P] [US4] Unit test for ElevenLabs client in backend/tests/unit/test_elevenlabs_client.py (test voice synthesis with retry logic, fallback to text-only mode)
- [ ] T068 [P] [US4] Unit test for interview LangGraph flow in backend/tests/unit/test_interview_service.py (test conversation state management, context preservation)
- [ ] T069 [P] [US4] Integration test for interview workflow in backend/tests/integration/test_interview_workflow.py (test end-to-end: start → Q&A loop → complete → analysis)

### Implementation for User Story 4

- [ ] T070 [P] [US4] Create MockInterview model in backend/src/models/mock_interview.py (SQLAlchemy ORM: id, user_id, resume_id, transcript JSON, performance_score, feedback TEXT, duration_seconds, created_at)
- [ ] T071 [P] [US4] Implement ElevenLabs API client in backend/src/api/elevenlabs_client.py with @retry_with_backoff decorator and text-only fallback (Constitution II: API Resilience)
- [ ] T072 [US4] Implement interview LangGraph workflow in backend/src/services/interview_service.py (StateGraph with nodes: generate_question, analyze_answer, generate_followup, finalize_feedback)
- [ ] T073 [US4] Create POST /interview/start endpoint in backend/src/routers/interview.py (create session, generate first question using Claude, synthesize voice with ElevenLabs, return question + audio_url)
- [ ] T074 [US4] Create POST /interview/answer endpoint in backend/src/routers/interview.py (accept answer, analyze with Claude, generate follow-up, return next question + audio in <2s)
- [ ] T075 [US4] Create GET /interview/{id}/transcript endpoint in backend/src/routers/interview.py (retrieve full transcript, performance analysis, recommendations)
- [ ] T076 [US4] Add performance monitoring to interview service (track response latency, log warning if >2s, measure p90 via structured logs)
- [ ] T077 [US4] Add graceful degradation for ElevenLabs failures (fallback to text-only mode, log voice_synthesis_failed, continue interview without audio)
- [ ] T078 [US4] Create frontend interview.html in frontend/src/interview.html (start button, question display with audio player, answer textarea, submit button, transcript view)
- [ ] T079 [US4] Create frontend interview.js in frontend/src/js/interview.js (handle session start, play audio questions, submit answers, display transcript, show performance analysis)
- [ ] T080 [US4] Add CSS styling for interview page in frontend/src/css/styles.css (interview interface, audio controls, transcript formatting)

**Checkpoint**: Mock interview functional. User can practice with AI interviewer, voice synthesis works with fallback, <2s latency achieved.

---

## Phase 7: User Story 5 - Application Dashboard (Priority: P3)

**Goal**: User views all applications, cover letters, interviews in one dashboard with timeline and stats

**Independent Test**: User opens dashboard → Sees all saved items → Can filter by date → View statistics

### Tests for User Story 5 (OPTIONAL - only if time permits) ⚠️

- [ ] T081 [P] [US5] Contract test for GET /dashboard in backend/tests/integration/test_dashboard_api.py (test dashboard data aggregation)
- [ ] T082 [P] [US5] Unit test for dashboard statistics in backend/tests/unit/test_dashboard_service.py (test metrics calculation: total applications, success rate, trends)

### Implementation for User Story 5

- [ ] T083 [US5] Create GET /dashboard endpoint in backend/src/routers/dashboard.py (aggregate resumes, cover letters, jobs, interviews for user, return summary stats)
- [ ] T084 [US5] Create frontend index.html in frontend/src/index.html (dashboard with cards for resumes, cover letters, jobs, interviews, timeline visualization)
- [ ] T085 [US5] Create frontend dashboard.js in frontend/src/js/dashboard.js (fetch dashboard data, render cards, implement date filtering, display statistics)
- [ ] T086 [US5] Add CSS styling for dashboard in frontend/src/css/styles.css (card layout, timeline, stats panels)

**Checkpoint**: All user stories complete. Full application functional with dashboard overview.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gates, security audit, performance testing, documentation

- [ ] T087 [P] Create README.md with setup instructions (Docker Compose setup, environment variables, running tests, demo guide)
- [ ] T088 [P] Create API documentation using FastAPI auto-generated docs (ensure all endpoints documented with examples)
- [ ] T089 Run pytest with coverage report (ensure 80% minimum coverage per Constitution V)
- [ ] T090 Run detect-secrets scan (ensure zero credential leaks per Constitution III)
- [ ] T091 [P] Create GitHub Actions CI workflow in .github/workflows/ci.yml (run tests, check coverage, credential scan, lint)
- [ ] T092 Security audit: Review all logs for PII exposure (check error messages, stack traces, debug logs)
- [ ] T093 Performance testing: Load test with 100 concurrent users using Locust or JMeter (verify <5% error rate per SC-003)
- [ ] T094 Performance testing: Verify cover letter generation p95 latency <60s (measure via structured logs per SC-001)
- [ ] T095 Performance testing: Verify mock interview p90 latency <2s (measure via performance monitoring per SC-002)
- [ ] T096 Create demo script for hackathon presentation (step-by-step narrative matching spec.md Demo Story)
- [ ] T097 [P] Frontend polish: Add loading spinners, error messages, success notifications
- [ ] T098 [P] Frontend polish: Add responsive CSS for mobile devices
- [ ] T099 Database optimization: Add indexes for frequently queried fields (user_id, created_at, status)
- [ ] T100 Add health check monitoring endpoint GET /health (return 200 OK with uptime, database connection status)

**Checkpoint**: Production-ready. All quality gates passed, performance validated, security audited, demo ready.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Resume Analysis (P1 CRITICAL for MVP)
- **User Story 2 (Phase 4)**: Depends on Foundational + User Story 1 (resume analysis) - Cover Letter Generation (P1 CRITICAL for MVP)
- **User Story 3 (Phase 5)**: Depends on Foundational - Job Discovery Agent (P2 - implement if time permits after P1 complete)
- **User Story 4 (Phase 6)**: Depends on Foundational - Mock Interview (P2 - implement if time permits after P1 complete)
- **User Story 5 (Phase 7)**: Depends on all prior user stories - Dashboard (P3 - defer unless P1/P2 complete)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅ MVP BLOCKER
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) + US1 models - Requires Resume model for resume_id reference ✅ MVP BLOCKER
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Independently testable, integrates with US2 for cover letter generation
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Independently testable, uses Resume model from US1
- **User Story 5 (P3)**: Requires US1, US2, US3, US4 data to display on dashboard

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Constitution V: Test-First)
- Models before services (database schema must exist)
- Services before endpoints (business logic must exist)
- Backend endpoints before frontend UI (API must be functional)
- Logging and monitoring added to all services (Constitution V: Structured Logging)
- PII scrubbing applied to all error handling (Constitution III: User Privacy)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005, T006)
- All Foundational tasks marked [P] can run in parallel (T008, T009, T010, T011, T012, T013, T015, T016)
- All tests for a user story marked [P] can run in parallel (e.g., T017-T021 for US1)
- All models marked [P] can run in parallel (e.g., T022, T023 for US1)
- **CRITICAL**: User Story 3 and User Story 4 can be implemented in parallel after Foundational phase completes (both P2 priority, no direct dependencies)

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all tests for User Story 1 together (MANDATORY per Constitution):
Task: "Contract test for POST /resume/upload in backend/tests/integration/test_resume_api.py"
Task: "Contract test for GET /resume/{id}/analysis in backend/tests/integration/test_resume_api.py"
Task: "Unit test for resume text extraction in backend/tests/unit/test_resume_service.py"
Task: "Unit test for Claude API retry logic in backend/tests/unit/test_claude_client.py"
Task: "Integration test for resume analysis workflow in backend/tests/integration/test_resume_workflow.py"

# Then launch all models for User Story 1 together:
Task: "Create Resume model in backend/src/models/resume.py"
Task: "Implement Claude API client in backend/src/api/claude_client.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only) - DAY 1 TARGET

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T016) - CRITICAL BLOCKER
3. Complete Phase 3: User Story 1 - Resume Analysis (T017-T033)
4. **STOP and VALIDATE**: Test User Story 1 independently, verify resume upload → analysis works
5. Complete Phase 4: User Story 2 - Cover Letter Generation (T034-T048)
6. **STOP and VALIDATE**: Test User Story 2 independently, verify resume → job description → cover letter works
7. **MVP DEMO READY**: Can demonstrate core value proposition

### Incremental Delivery - DAY 2 IF TIME PERMITS

1. Complete MVP First → Foundation ready
2. Add User Story 3 - Job Discovery Agent (T049-T063) → Test independently → Validate LangGraph autonomous search
3. Add User Story 4 - Mock Interview (T064-T080) → Test independently → Validate voice synthesis + <2s latency
4. Add User Story 5 - Dashboard (T081-T086) → Test independently → Polish UX
5. Complete Phase 8: Polish (T087-T100) → Security audit, performance testing, documentation

### Parallel Team Strategy (If Multiple Developers Available)

With 2-3 developers after Foundational phase completes:

1. **Team completes Setup + Foundational together** (T001-T016)
2. **Once Foundational is done:**
   - **Developer A**: User Story 1 - Resume Analysis (T017-T033) - P1 CRITICAL
   - **Developer B**: User Story 2 - Cover Letter Generation (T034-T048) - P1 CRITICAL (can start models in parallel with US1)
3. **After P1 complete:**
   - **Developer A**: User Story 3 - Job Discovery Agent (T049-T063) - P2
   - **Developer B**: User Story 4 - Mock Interview (T064-T080) - P2
   - **Developer C**: Polish & Testing (T087-T100)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story (US1-US5) for traceability
- Each user story should be independently completable and testable
- **CRITICAL**: All tests must be written FIRST and FAIL before implementation (Constitution V: Test-First)
- Verify tests fail before implementing (Red-Green-Refactor cycle)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution compliance required: retry logic (T008), PII scrubbing (T010), structured logging (T011), 80% coverage (T089)
- MVP = P1 features only (Resume Analysis + Cover Letter Generation) - 48 tasks (T001-T048)
- P2 features (Job Discovery + Mock Interview) - 32 additional tasks (T049-T080) - implement ONLY if P1 complete
- P3 features (Dashboard) - 6 additional tasks (T081-T086) - defer unless all P1/P2 complete
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Hackathon Strategy**: Ruthlessly prioritize P1, defer P2/P3, accept technical debt if documented
