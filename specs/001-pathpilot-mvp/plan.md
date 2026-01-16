# Implementation Plan: PathPilot Job Application Automation

**Branch**: `001-pathpilot-mvp` | **Date**: 2025-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-pathpilot-mvp/spec.md`

## Summary

PathPilot automates job applications using AI agents for resume analysis, cover letter generation, job discovery, and mock interviews. Technical approach combines LangGraph for autonomous workflows, Claude API for content generation/analysis, ElevenLabs for voice synthesis, and Python FastAPI backend with PostgreSQL storage. MVP focuses on P1 features (resume analysis + cover letter generation) with retry logic and structured logging throughout.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, LangGraph, LangChain, Anthropic Claude SDK, ElevenLabs SDK, SQLAlchemy, PyPDF2, python-docx
**Storage**: PostgreSQL 15+ (users, resumes, jobs, cover_letters, interviews tables)
**Testing**: pytest, pytest-cov (80% coverage target), pytest-asyncio for async handlers
**Target Platform**: Linux server (Docker containerized), deployed to cloud (AWS/GCP/Render)
**Project Type**: Web application (backend API + frontend client)
**Performance Goals**: <60s cover letter generation (p95), <2s mock interview latency (p90), 100 concurrent users
**Constraints**: 95% uptime during demo, zero credential leaks, all external APIs have retry logic
**Scale/Scope**: MVP with 5 user stories, ~15 API endpoints, 5 database tables, 2 external API integrations (Claude + ElevenLabs)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Agentic AI First ✅ PASS

- **Requirement**: Use LangGraph for autonomous workflows
- **Implementation**: Job discovery agent (US3) uses LangGraph StateGraph with nodes for search, filter, rank
- **Validation**: Resume analysis (US1) and cover letter generation (US2) use LangChain prompts; mock interview (US4) uses LangGraph conversation flow

### II. External API Resilience ✅ PASS

- **Requirement**: All Claude/ElevenLabs calls have retry logic with exponential backoff
- **Implementation**:
  - Create `api/retry_wrapper.py` with decorator `@retry_with_backoff(attempts=3, backoff=[1, 2, 4])`
  - Apply to all Claude API calls (resume analysis, cover letter generation, interview questions)
  - Apply to all ElevenLabs API calls (voice synthesis) with fallback to text-only mode
  - Implement circuit breaker for job board APIs in `api/circuit_breaker.py`
- **Validation**: Integration tests verify retry behavior on simulated API failures

### III. User Data Privacy ✅ PASS

- **Requirement**: No credential leaks, secure storage required
- **Implementation**:
  - API keys stored in `.env` file (never committed): `ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`
  - Use `python-dotenv` to load environment variables
  - Implement PII scrubbing in `utils/privacy.py` (regex patterns for SSN, phone, email in logs)
  - Add pre-commit hook with `detect-secrets` to scan for credential leaks
  - Resume file storage uses secure file paths with UUID filenames (not original names in public URLs)
- **Validation**: Security audit before demo, credential scanning in CI/CD

### IV. Hackathon MVP First ✅ PASS

- **Requirement**: 2-day focus, core features only
- **Implementation**:
  - **Day 1 Priority**: P1 features (Resume Analysis + Cover Letter Generation) - these are the demo story
  - **Day 2 Priority**: P2 features (Job Discovery + Mock Interview) if time permits, otherwise defer
  - **Deferred**: P3 features (Dashboard stats/timeline visualization) - nice-to-have only
  - Technical debt accepted: Frontend uses basic HTML/JS (no React), database migrations manual (no Alembic initially)
- **Validation**: Feature flags to toggle P2/P3 features, daily standups to reassess scope

### V. Code Quality ✅ PASS

- **Requirement**: 80% test coverage, structured logging
- **Implementation**:
  - Unit tests for all services (`tests/unit/test_resume_service.py`, `tests/unit/test_cover_letter_service.py`)
  - Integration tests for API endpoints (`tests/integration/test_api.py`)
  - Structured logging with `structlog` library: all logs include `request_id`, `user_id`, `operation`, `duration_ms`
  - Coverage measured with `pytest-cov --cov=src --cov-report=html`
- **Validation**: CI enforces 80% coverage gate before merge, manual log review during testing

## Project Structure

### Documentation (this feature)

```text
specs/001-pathpilot-mvp/
├── plan.md              # This file
├── spec.md              # Feature specification (COMPLETED)
├── research.md          # Phase 0 output (PENDING - will document LangGraph patterns, API research)
├── data-model.md        # Phase 1 output (PENDING - will define database schema)
├── contracts/           # Phase 1 output (PENDING - will define API contracts)
│   ├── resume-analysis.md
│   ├── cover-letter.md
│   └── mock-interview.md
└── tasks.md             # Phase 2 output (NOT created yet - use /speckit.tasks)
```

### Source Code (repository root)

```text
# Web application structure (backend + frontend)

backend/
├── src/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Environment variable loading, settings
│   ├── database.py                # SQLAlchemy setup, session management
│   ├── models/                    # Database models (SQLAlchemy ORM)
│   │   ├── user.py
│   │   ├── resume.py
│   │   ├── job_posting.py
│   │   ├── cover_letter.py
│   │   └── mock_interview.py
│   ├── services/                  # Business logic layer
│   │   ├── resume_service.py      # Resume upload, text extraction, Claude analysis
│   │   ├── cover_letter_service.py # Cover letter generation logic
│   │   ├── job_discovery_agent.py # LangGraph autonomous agent
│   │   └── interview_service.py   # Mock interview orchestration
│   ├── api/                       # External API integrations
│   │   ├── claude_client.py       # Anthropic Claude wrapper with retry logic
│   │   ├── elevenlabs_client.py   # ElevenLabs wrapper with retry logic
│   │   ├── retry_wrapper.py       # Retry decorator implementation
│   │   └── circuit_breaker.py     # Circuit breaker pattern
│   ├── routers/                   # FastAPI route handlers
│   │   ├── resume.py              # POST /resume/upload, GET /resume/{id}/analysis
│   │   ├── cover_letter.py        # POST /cover-letter/generate
│   │   ├── jobs.py                # GET /jobs, POST /jobs/search
│   │   └── interview.py           # POST /interview/start, POST /interview/answer
│   └── utils/
│       ├── privacy.py             # PII scrubbing functions
│       ├── file_handler.py        # Resume file upload/storage
│       └── logging_config.py      # Structured logging setup
├── tests/
│   ├── unit/
│   │   ├── test_resume_service.py
│   │   ├── test_cover_letter_service.py
│   │   ├── test_claude_client.py
│   │   └── test_privacy.py
│   ├── integration/
│   │   ├── test_resume_api.py
│   │   ├── test_cover_letter_api.py
│   │   └── test_retry_logic.py
│   └── conftest.py                # Pytest fixtures
├── alembic/                       # Database migrations (deferred to Day 2)
├── .env.example                   # Template for environment variables
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container setup
└── pytest.ini                     # Test configuration

frontend/
├── src/
│   ├── index.html                 # Dashboard page
│   ├── resume.html                # Resume upload page
│   ├── cover-letter.html          # Cover letter generation page
│   ├── interview.html             # Mock interview interface
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── api-client.js          # Fetch wrappers for backend API
│       ├── resume.js              # Resume upload handling
│       ├── cover-letter.js        # Cover letter generation UI
│       └── interview.js           # Interview session management
└── package.json                   # Frontend dependencies (minimal - no build step for MVP)

.github/
└── workflows/
    └── ci.yml                     # GitHub Actions: run tests, check coverage, credential scan

.pre-commit-config.yaml            # detect-secrets hook configuration
docker-compose.yml                 # PostgreSQL + backend services
README.md                          # Setup instructions, demo guide
```

**Structure Decision**: Web application structure selected because feature requires both backend API (for AI processing, database) and frontend interface (for user interactions). Backend serves FastAPI REST endpoints, frontend is simple HTML/JS (no framework) to minimize complexity for 2-day hackathon timeline. Docker Compose orchestrates PostgreSQL database and backend service for easy local development and deployment.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A - All constitution requirements met | - | - |

## Phase 0: Research (Next Step)

**Objective**: Document LangGraph workflow patterns, Claude API prompt engineering, ElevenLabs voice synthesis integration.

**Deliverable**: `research.md` containing:
- LangGraph StateGraph example for job discovery agent
- Claude API prompt templates for resume analysis and cover letter generation
- ElevenLabs voice synthesis latency benchmarks and fallback strategies
- PostgreSQL schema design considerations for JSON storage (resume analysis results)
- Retry logic implementation patterns (exponential backoff, circuit breaker)

**Command**: `/speckit.plan` will generate this automatically in next phase.

## Phase 1: Design (After Research)

**Objective**: Define database schema, API contracts, and data flow diagrams.

**Deliverables**:
- `data-model.md`: PostgreSQL table schemas with relationships
- `contracts/resume-analysis.md`: POST /resume/upload and GET /resume/{id}/analysis API specs
- `contracts/cover-letter.md`: POST /cover-letter/generate API spec
- `contracts/mock-interview.md`: POST /interview/start and POST /interview/answer API specs
- `quickstart.md`: Local setup guide for developers

**Command**: `/speckit.plan` will generate these after research phase.

## Phase 2: Task Breakdown (After Design)

**Objective**: Convert design into executable tasks organized by user story.

**Deliverable**: `tasks.md` with phases:
- Phase 1: Setup (project structure, dependencies, database)
- Phase 2: Foundational (API retry wrappers, logging, auth)
- Phase 3: User Story 1 - Resume Analysis (tests → models → service → API)
- Phase 4: User Story 2 - Cover Letter Generation (tests → service → API)
- Phase 5: User Story 3 - Job Discovery Agent (if time permits)
- Phase 6: User Story 4 - Mock Interview (if time permits)
- Phase 7: Polish (security audit, performance testing, documentation)

**Command**: `/speckit.tasks` will generate this after design phase.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Claude API rate limits during demo | HIGH - demo fails if API quota exhausted | Pre-load API credits, implement request queuing, cache analysis results |
| ElevenLabs voice latency >2s | MEDIUM - interview experience degraded | Fallback to text-only mode, pre-generate common responses, use streaming API |
| Resume parsing fails on non-standard PDFs | MEDIUM - users can't upload resumes | Support DOCX as alternative, add manual text paste option, handle errors gracefully |
| 100 concurrent users exceed database capacity | HIGH - system crashes during demo | Load test with JMeter, add connection pooling, implement rate limiting |
| Credential leak in logs | CRITICAL - disqualification from hackathon | Automated credential scanning in pre-commit hooks, log audit before demo |
| Scope creep on P2/P3 features | HIGH - P1 features incomplete | Daily scope review, feature flags to disable incomplete features, ruthless prioritization |

## Success Metrics (Aligned with Spec)

- ✅ **SC-001**: Cover letter generation <60s (95th percentile) - measured via structured logs
- ✅ **SC-002**: Mock interview latency <2s (90th percentile) - measured via performance monitoring
- ✅ **SC-003**: 100 concurrent users with <5% error rate - validated via load testing
- ✅ **SC-004**: 95% uptime during demo window - measured via health check endpoint
- ✅ **SC-005**: Zero credential leaks - validated via pre-commit scanning
- ✅ **SC-007**: 100% retry logic coverage on external APIs - validated via integration tests
- ✅ **SC-008**: 80% test coverage minimum - enforced via CI gate

## Next Steps

1. Run `/speckit.plan` to generate Phase 0 research documentation
2. Review research findings and validate technical approach
3. Run `/speckit.plan` again to generate Phase 1 design artifacts (data-model.md, contracts/)
4. Validate API contracts against constitution requirements
5. Run `/speckit.tasks` to generate executable task breakdown
6. Begin implementation with P1 features (Resume Analysis → Cover Letter Generation)
