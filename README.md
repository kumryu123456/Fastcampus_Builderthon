# 🎯 PathPilot

AI-powered job application automation platform built for the Builderthon Hackathon.

## Features

- **📄 Resume Analysis**: Upload your resume and get AI-powered insights on strengths, weaknesses, and recommendations
- **✍️ Cover Letter Generation**: Generate personalized cover letters in under 60 seconds
- **🔍 Job Discovery** (P2): Autonomous AI agent finds matching job postings
- **🎤 Mock Interviews** (P2): Practice with AI interviewer powered by voice synthesis
- **📊 Application Dashboard** (P3): Track all applications with timeline and statistics

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **AI**: Google Gemini, LangGraph, LangChain
- **Voice**: ElevenLabs
- **Database**: PostgreSQL 15+
- **Cache**: Redis
- **Frontend**: HTML/CSS/JavaScript (vanilla - hackathon MVP)

> **Note on AI Provider**: This project uses Google Gemini as the primary AI provider. The architecture supports multiple LLM providers through LangChain, making it easy to switch between Gemini, Claude, or other models. Original specifications referenced Claude, but implementation is provider-agnostic.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Google Gemini API key ([get here](https://aistudio.google.com/app/apikey))
- ElevenLabs API key ([get here](https://elevenlabs.io/))

### Setup

1. **Clone and configure**

```bash
git clone <your-repo>
cd pathpilot

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

2. **Start services**

```bash
# Start PostgreSQL, Redis, and backend
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

3. **Access the application**

- Frontend: Open `frontend/src/index.html` in your browser
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Development Setup (Without Docker)

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up database
createdb pathpilot  # or use Docker for PostgreSQL only

# Run migrations (once implemented)
# alembic upgrade head

# Start backend
uvicorn src.main:app --reload

# Frontend
# Simply open frontend/src/index.html in your browser
# For production, use a simple HTTP server:
cd frontend/src
python -m http.server 3000
```

## Project Structure

```
pathpilot/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Environment configuration
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/              # Database models
│   │   ├── services/            # Business logic
│   │   ├── api/                 # External API clients
│   │   ├── routers/             # API endpoints
│   │   └── utils/               # Utilities (logging, privacy)
│   ├── tests/                   # Test files
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── index.html           # Dashboard
│       ├── resume.html          # Resume upload
│       ├── cover-letter.html    # Cover letter generator
│       ├── jobs.html            # Job discovery
│       ├── interview.html       # Mock interview
│       ├── css/
│       └── js/
├── specs/                       # Specification documents
├── docker-compose.yml
├── .env.example
└── README.md
```

## Constitution Principles

This project follows 5 core principles:

1. **Agentic AI First**: LangGraph for autonomous workflows
2. **External API Resilience**: Retry logic with exponential backoff
3. **User Data Privacy**: No credential leaks, secure storage
4. **Hackathon MVP First**: 2-day focus, core features only
5. **Code Quality**: 80% test coverage, structured logging

See `.specify/memory/constitution.md` for details.

## Development Workflow

### Phase 1: MVP (P1 Features) - Day 1

- [x] Setup (T001-T006)
- [ ] Foundational (T007-T016): Database, retry logic, logging
- [ ] User Story 1 (T017-T033): Resume upload & analysis
- [ ] User Story 2 (T034-T048): Cover letter generation

### Phase 2: Enhanced Features (P2) - Day 2 (if time permits)

- [ ] User Story 3 (T049-T063): Job discovery agent
- [ ] User Story 4 (T064-T080): Mock interview

### Phase 3: Polish (P3)

- [ ] User Story 5 (T081-T086): Dashboard stats
- [ ] Testing & security audit (T087-T100)

## Testing

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_resume_service.py

# View coverage report
open htmlcov/index.html
```

## API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Key Endpoints (MVP)

```
POST /resume/upload           # Upload resume for analysis
GET  /resume/{id}/analysis    # Get resume analysis results
POST /cover-letter/generate   # Generate cover letter
GET  /cover-letter/{id}       # Get cover letter
PUT  /cover-letter/{id}/edit  # Update cover letter
GET  /health                  # Health check
```

## Security

- **API Keys**: Stored in environment variables only (never in code)
- **PII Scrubbing**: SSN, phone, email removed from logs
- **Credential Scanning**: Pre-commit hooks with `detect-secrets`
- **File Upload**: UUID filenames, validated types (PDF/DOCX only)

## Performance Targets

- Cover letter generation: **<60 seconds** (p95)
- Mock interview response: **<2 seconds** (p90)
- Concurrent users: **100 users** with <5% error rate
- Uptime: **95%** during demo

## Troubleshooting

### Docker issues

```bash
# Reset everything
docker-compose down -v
docker-compose up --build

# Check container logs
docker-compose logs backend
docker-compose logs postgres
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U pathpilot -d pathpilot
```

### API key issues

```bash
# Verify .env file exists and has keys
cat .env | grep API_KEY

# Restart backend to reload environment
docker-compose restart backend
```

## Demo Script

For hackathon presentation, follow this narrative:

1. **Opening**: "Meet Sarah, a software engineer looking for her next role..."
2. **Resume Upload**: Upload resume → Show AI analysis (strengths/weaknesses)
3. **Cover Letter**: Paste job description → Generate personalized letter in <60s
4. **Mock Interview** (if P2 complete): Start interview → AI asks questions with voice
5. **Dashboard**: Show application tracking and statistics

## Contributing

This is a hackathon project. For post-hackathon contributions:

1. Follow test-first development (write tests before code)
2. Ensure 80% test coverage
3. Add structured logging to new features
4. Run security scan: `detect-secrets scan`
5. Check constitution compliance in `specs/001-pathpilot-mvp/plan.md`

## License

MIT License - Built for Builderthon Hackathon 2025

## Team

- Your team members here

## Acknowledgments

- Google Gemini for AI capabilities
- ElevenLabs for voice synthesis
- LangGraph for agentic workflows
- Builderthon Hackathon organizers

---

**Status**: Phase 1 Setup Complete ✅ | Ready for Foundational Development

**Next**: Implement T007-T016 (Database, retry logic, logging, auth)
