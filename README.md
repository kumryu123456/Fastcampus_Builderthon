# 🧭 PathPilot — AI 취업 지원 어시스턴트

> **패스트캠퍼스 빌더톤(Builderthon) 2025 참가작**
> AI 기반 이력서 분석 · 자기소개서 생성 · 채용 추천 · 모의 면접 All-in-One 서비스

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Gemini](https://img.shields.io/badge/Google-Gemini_API-4285F4?style=flat-square&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)

---

## 📌 프로젝트 개요

취업 준비생이 하나의 플랫폼에서 이력서 분석부터 모의 면접까지 완결할 수 있는
**AI 취업 지원 통합 어시스턴트**입니다.

패스트캠퍼스 빌더톤에서 백엔드를 단독 설계·구현하였으며,
FastAPI + PostgreSQL + Google Gemini API를 활용한 AI 기능 4종을 완성하였습니다.

---

## 🏆 주요 성과

| 기능 | 목표 응답시간 | 실측 응답시간 |
|------|-------------|-------------|
| 이력서 분석 | < 60초 | **~13초** |
| 자기소개서 생성 | < 60초 | **~12초** |
| 채용 추천 | < 30초 | **~10초** |
| 모의 면접 질문 생성 | < 15초 | **~12초** |
| 면접 답변 평가 | < 10초 | **~14초** |

> 목표 응답시간 4/5 항목 달성, 1항목(면접 답변 평가)은 소폭 초과

---

## 🎯 내가 기여한 부분

- **백엔드 단독 설계 및 구현**: FastAPI 기반 RESTful API 16개 엔드포인트 구현
- **AI 서비스 레이어**: Google Gemini API 연동으로 이력서 분석·자소서 생성·면접 질문·답변 평가 로직 구현
- **데이터베이스 설계**: SQLAlchemy ORM 기반 DB 모델 설계 (이력서, 자소서, 채용공고, 면접 히스토리)
- **Docker 환경 구성**: docker-compose로 PostgreSQL 15 + FastAPI 개발 환경 표준화
- **API 문서화**: FastAPI 자동 Swagger UI 구성 및 엔드포인트 정의

---

## 🏗️ 시스템 아키텍처

```
[Frontend: Vanilla HTML/CSS/JS]
         |
         v
[FastAPI Backend (Python 3.12)]
  ├── /api/v1/resume       <- 이력서 업로드 & AI 분석
  ├── /api/v1/cover-letter <- 자기소개서 AI 생성
  ├── /api/v1/jobs         <- 채용공고 AI 추천
  └── /api/v1/interview    <- 모의 면접 질문/평가
         |
    ┌────┴────┐
    |         |
[PostgreSQL 15]  [Google Gemini API]
(Docker)         (AI 처리 핵심)
```

---

## ✨ 핵심 기능 4종

**1. 이력서 AI 분석** - PDF/DOCX 업로드 → Gemini API로 강점·약점·개선 추천 자동 생성

**2. 자기소개서 AI 생성** - 이력서 분석 결과 기반 맞춤형 자소서, 톤/길이 옵션 지원, 재생성 기능

**3. 채용공고 AI 추천** - 이력서 내용 기반 적합 포지션 추천 및 매칭 스코어 분석

**4. 모의 면접** - 이력서 기반 예상 질문 자동 생성 + 사용자 답변 AI 평가 및 피드백

---

## ⚙️ 기술 스택

| 영역 | 기술 |
|------|------|
| Backend Framework | FastAPI, Python 3.12 |
| Database | PostgreSQL 15 (Docker), SQLAlchemy ORM |
| AI | Google Gemini API |
| Frontend | HTML/CSS/JavaScript (Vanilla) |
| DevOps | Docker, docker-compose |
| 문서화 | Swagger UI (FastAPI 자동 생성) |

---

## 🚀 로컬 실행 방법

```bash
# 1. 레포 클론
git clone https://github.com/kumryu123456/Fastcampus_Builderthon.git
cd Fastcampus_Builderthon

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 GOOGLE_API_KEY 입력

# 3. PostgreSQL 실행 (Docker)
docker-compose up -d postgres

# 4. 백엔드 실행
cd backend
python -m venv venv
pip install -r requirements.txt
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 5. 프론트엔드 실행
cd ../frontend
python -m http.server 8080
```

접속 주소: 프론트엔드 http://localhost:8080 / API 문서(Swagger) http://localhost:8000/docs

---

## 📁 프로젝트 구조

```
Fastcampus_Builderthon/
├── backend/
│   └── src/
│       ├── main.py        # FastAPI 앱 진입점
│       ├── models/        # SQLAlchemy DB 모델
│       ├── services/      # 비즈니스 로직 + Gemini AI
│       ├── routers/       # API 라우터 (4개 도메인)
│       └── utils/         # 로깅, 개인정보 처리
├── frontend/
│   ├── index.html         # 대시보드
│   ├── resume.html        # 이력서 업로드
│   ├── cover-letter.html  # 자소서 생성
│   ├── jobs.html          # 채용 추천
│   └── interview.html     # 모의 면접
├── docker-compose.yml
└── .env.example
```

---

## 📝 회고

> 빌더톤이라는 짧은 시간 안에 AI 기능 4종을 탑재한 서비스를 백엔드 단독으로 기획·구현했습니다.
> 핵심 과제는 **Gemini API의 응답 지연 관리**였고, 비동기 처리를 통해
> 대부분의 기능에서 목표 응답시간을 달성하였습니다.
> FastAPI의 자동 문서화 덕분에 프론트엔드와의 협업 효율도 크게 높일 수 있었습니다.
