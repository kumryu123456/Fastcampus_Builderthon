# PathPilot — AI 취업 지원 어시스턴트

패스트캠퍼스 빌더톤(Builderthon) 2026 참가작
이력서 분석 · 자기소개서 생성 · 채용 추천 · 모의 면접 All-in-One

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Gemini](https://img.shields.io/badge/Google-Gemini_API-4285F4?style=flat-square&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)

---

## 프로젝트 소개

취업 준비생이 이력서 분석부터 모의 면접까지 하나의 서비스에서 처리할 수 있는 AI 어시스턴트입니다. 빌더톤에서 백엔드 전체를 단독으로 기획하고 구현했으며, Google Gemini API를 연동한 AI 기능 4종을 완성했습니다.

---

## 응답시간 측정 결과

| 기능 | 목표 | 실측 | 결과 |
|------|------|------|------|
| 이력서 분석 | < 60초 | 90초 → 13초 (85% 단축) | 달성 |
| 자기소개서 생성 | < 60초 | ~12초 | 달성 |
| 채용 추천 | < 30초 | ~10초 | 달성 |
| 모의 면접 질문 생성 | < 15초 | ~12초 | 달성 |
| 면접 답변 평가 | < 10초 | ~14초 | 미달 (4초 초과) |

5개 중 4개 항목 목표 달성. 면접 답변 평가는 Gemini API 응답 지연이 원인이었습니다.

---

## 담당 역할

백엔드 단독 설계 및 구현을 담당했습니다.

- FastAPI 기반 RESTful API 16개 엔드포인트 구현
- Google Gemini API 연동 — 이력서 분석, 자소서 생성, 면접 질문/답변 평가 로직
- SQLAlchemy ORM 기반 DB 모델 설계 (이력서, 자소서, 채용공고, 면접 히스토리) — 총 15개
- docker-compose로 PostgreSQL 15 + FastAPI 개발 환경 구성
- FastAPI Swagger UI 기반 API 문서 자동화

---

## 아키텍처

```
[Frontend: Vanilla HTML/CSS/JS]
          |
[FastAPI Backend (Python 3.12)]
 ├── /api/v1/resume        이력서 업로드 & AI 분석
 ├── /api/v1/cover-letter  자기소개서 AI 생성
 ├── /api/v1/jobs          채용공고 AI 추천
 └── /api/v1/interview     모의 면접 질문/평가
          |
[PostgreSQL 15 (Docker)]   [Google Gemini API]
```

---

## 기능 상세

**이력서 AI 분석** — PDF/DOCX 업로드 → Gemini API로 강점, 약점, 개선 방향 자동 분석

**자기소개서 AI 생성** — 이력서 분석 결과 기반 맞춤형 자소서 생성. 톤(formal/casual)과 길이 옵션 지원, 재생성 가능

**채용공고 AI 추천** — 이력서 내용 기반 적합 포지션 추천 및 매칭 스코어 분석

**모의 면접** — 이력서 기반 예상 질문 자동 생성, 사용자 답변 입력 시 AI 평가 및 피드백 제공

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 15, SQLAlchemy ORM |
| AI | Google Gemini API |
| Frontend | HTML/CSS/JavaScript (Vanilla) |
| DevOps | Docker, docker-compose |

---

## 기술 선택 이유

**FastAPI** — 빌더톤 기간이 짧아 빠른 개발이 필수였습니다. Django/Flask 대비 비동기 처리가 기본이고 Pydantic 덕분에 요청/응답 스키마를 별도 코드 없이 자동 검증할 수 있어서 선택했습니다. Swagger 문서 자동 생성도 프론트엔드 팀원과 협업할 때 유용했습니다.

**Google Gemini API** — OpenAI GPT와 비교했을 때 당시 무료 할당량이 더 넉넉했습니다. 빌더톤처럼 비용 제약이 있는 상황에서 Gemini Flash 모델의 속도와 무료 티어 한도가 적합했습니다. 다만 GPT-4 계열 대비 한국어 자소서 품질이 낮은 건 단점이었습니다.

**SQLAlchemy ORM + PostgreSQL** — 이력서, 자소서, 면접 히스토리 간 관계가 복잡해서 ORM 없이 raw SQL로 관리하면 실수가 나기 쉽습니다. SQLAlchemy의 관계 매핑으로 엔티티 간 연관을 명확히 하고, Docker로 환경을 통일해 팀원들이 로컬에서 동일한 DB 환경을 쓸 수 있도록 했습니다.

---

## 실행 방법

```bash
git clone https://github.com/kumryu123456/Fastcampus_Builderthon.git
cd Fastcampus_Builderthon

cp .env.example .env
# .env에 GOOGLE_API_KEY 입력

docker-compose up -d postgres

cd backend
python -m venv venv
pip install -r requirements.txt
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 별도 터미널에서
cd frontend
python -m http.server 8080
```

프론트엔드: http://localhost:8080
API 문서(Swagger): http://localhost:8000/docs

---

## 프로젝트 구조

```
Fastcampus_Builderthon/
├── backend/
│   └── src/
│       ├── main.py      FastAPI 앱 진입점
│       ├── models/      SQLAlchemy DB 모델
│       ├── services/    비즈니스 로직 + Gemini AI
│       ├── routers/     API 라우터 (4개 도메인)
│       └── utils/       로깅, 개인정보 처리
├── frontend/
│   ├── index.html       대시보드
│   ├── resume.html      이력서 업로드
│   ├── cover-letter.html 자소서 생성
│   ├── jobs.html        채용 추천
│   └── interview.html   모의 면접
├── docker-compose.yml
└── .env.example
```

---

## 회고

빌더톤 특성상 짧은 시간 안에 기획부터 구현까지 해야 했습니다. 백엔드를 혼자 맡으면서 AI 기능 4종을 동시에 개발하는 게 쉽지 않았는데, FastAPI의 의존성 주입 구조 덕분에 각 기능을 독립적으로 개발하고 붙이는 방식으로 속도를 낼 수 있었습니다.

면접 답변 평가 응답시간이 목표를 초과한 건 아쉽습니다. Gemini API를 비동기로 처리하고 있었는데, 답변 평가는 입력 텍스트 길이가 길어져서 처리 시간이 더 걸리는 구조적인 문제였습니다. 스트리밍 응답으로 개선할 수 있을 것 같아 추후에 수정해볼 계획입니다.
