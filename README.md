# PathPilot

AI-powered job application assistant built for Builderthon Hackathon 2025.

## Features

| Feature | Description | Status |
|---------|-------------|--------|
| Resume Analysis | AI-powered resume analysis with strengths, weaknesses, and recommendations | ✅ Complete |
| Cover Letter | Personalized cover letter generation with tone/length options | ✅ Complete |
| Job Discovery | AI job recommendations based on resume analysis | ✅ Complete |
| Mock Interview | AI-generated interview questions with answer evaluation | ✅ Complete |

## Tech Stack

- **Backend**: FastAPI, Python 3.12
- **Database**: PostgreSQL 15 (Docker)
- **AI**: Google Gemini API
- **Frontend**: HTML/CSS/JavaScript (Vanilla)

## Quick Start

### Prerequisites

- Docker
- Python 3.12+
- Google Gemini API key

### 1. Clone and Configure

```bash
git clone <your-repo>
cd pathpilot

# Configure environment
cp .env.example .env
# Edit .env and add GOOGLE_API_KEY
```

### 2. Start PostgreSQL

```bash
docker-compose up -d postgres
```

### 3. Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start Frontend

```bash
cd frontend
python -m http.server 8080
```

### 5. Access

- **Frontend**: http://localhost:8080
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Resume Analysis
```
POST /api/v1/resume/upload          Upload and analyze resume (PDF/DOCX)
GET  /api/v1/resume/{id}/analysis   Get analysis results
```

### Cover Letter
```
POST /api/v1/cover-letter/generate  Generate cover letter
GET  /api/v1/cover-letter/{id}      Get cover letter
PUT  /api/v1/cover-letter/{id}      Update/regenerate
GET  /api/v1/cover-letter/          List all cover letters
```

### Job Discovery
```
POST /api/v1/jobs/recommend         Get job recommendations
POST /api/v1/jobs/match             Analyze job-resume match
POST /api/v1/jobs/                  Save a job
GET  /api/v1/jobs/{id}              Get job details
```

### Mock Interview
```
POST /api/v1/interview/generate-questions     Generate interview questions
POST /api/v1/interview/{id}/evaluate-answer   Evaluate answer
GET  /api/v1/interview/{id}                   Get interview details
GET  /api/v1/interview/                       List interview history
```

## Project Structure

```
pathpilot/
├── backend/
│   ├── src/
│   │   ├── main.py           # FastAPI app
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── models/           # DB models
│   │   ├── services/         # Business logic + Gemini
│   │   ├── routers/          # API endpoints
│   │   └── utils/            # Logging, privacy
│   └── requirements.txt
├── frontend/
│   ├── index.html            # Dashboard
│   ├── resume.html           # Resume upload
│   ├── cover-letter.html     # Cover letter generator
│   ├── jobs.html             # Job discovery
│   ├── interview.html        # Mock interview
│   ├── css/                  # Styles
│   └── js/                   # Client logic
├── docker-compose.yml
├── .env.example
└── README.md
```

## Performance

| Feature | Target | Actual |
|---------|--------|--------|
| Resume Analysis | <60s | ~13s |
| Cover Letter | <60s | ~12s |
| Job Recommendations | <30s | ~10s |
| Interview Questions | <15s | ~12s |
| Answer Evaluation | <10s | ~14s |

## Development Phases

- [x] **Phase 1**: Project setup
- [x] **Phase 2**: Infrastructure (Docker, PostgreSQL, logging)
- [x] **Phase 3**: Resume Analysis
- [x] **Phase 4**: Cover Letter Generation
- [x] **Phase 5**: Job Discovery
- [x] **Phase 6**: Mock Interview

## Environment Variables

```env
# Required
GOOGLE_API_KEY=your-gemini-api-key

# Optional
DATABASE_URL=postgresql://pathpilot:pathpilot@localhost:5432/pathpilot
APP_ENV=development
LOG_LEVEL=INFO
```

## License

MIT License - Builderthon Hackathon 2025
