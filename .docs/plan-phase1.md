# K-Lyric AI — Phase 1 MVP 구현 계획

> 임시 계획 문서. 구현 완료 후 삭제 가능.

## Context

`phase1.txt` 스펙 기반 K-POP 가사로 한국어를 학습하는 모바일 퍼스트 플랫폼.

**사용자 확인 사항:**
- **범위**: Phase 1 MVP만 구현 (Phase 2/3는 향후 확장)
- **AI**: LM Studio(gemma/qwen SLLM) 기본 + OpenRouter API 폴백
- **DB**: 로컬 Docker PostgreSQL + pgvector

---

## 폴더 구조

```
c:\mydev\K-Lyric-AI\
├── frontend/                    # Next.js 14 App Router
│   ├── app/
│   │   ├── (auth)/             # 로그인/회원가입
│   │   ├── songs/              # 가사 학습 화면
│   │   ├── tutor/              # AI 튜터 채팅
│   │   ├── practice/           # 발음 연습
│   │   ├── profile/            # 학습 추적/대시보드
│   │   └── layout.tsx
│   ├── components/
│   │   ├── lyrics/             # 가사 표시 컴포넌트
│   │   ├── chat/               # AI 튜터 채팅 UI
│   │   ├── pronunciation/      # 발음 연습 UI
│   │   └── ui/                 # 공통 UI 컴포넌트
│   ├── lib/
│   │   ├── api.ts              # React Query + API 클라이언트
│   │   └── store.ts            # Zustand 상태 관리
│   ├── public/                 # PWA manifest, icons
│   ├── next.config.js          # PWA 설정
│   ├── tailwind.config.js
│   └── package.json
│
├── backend/                    # FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   ├── songs.py        # 가사 CRUD API
│   │   │   ├── tutor.py        # AI 튜터 채팅 API
│   │   │   ├── pronunciation.py # 발음 평가 API
│   │   │   └── learning.py     # 학습 추적 API
│   │   ├── core/
│   │   │   ├── config.py       # 환경 설정
│   │   │   └── database.py     # DB 연결
│   │   ├── models/             # SQLAlchemy 모델
│   │   ├── schemas/            # Pydantic 스키마
│   │   ├── services/
│   │   │   ├── ai_service.py   # AI 추상화 레이어 (LM Studio + OpenRouter 폴백)
│   │   │   ├── rag_service.py  # RAG 파이프라인
│   │   │   ├── whisper_service.py # Whisper STT
│   │   │   └── lyrics_service.py  # 가사 처리
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml           # PostgreSQL + pgvector + Redis
├── .env.example
└── .docs/                       # 임시 계획 문서 (이 폴더)
```

---

## 데이터베이스 스키마

### songs — 노래 정보
```sql
id SERIAL PRIMARY KEY,
title VARCHAR(255),
artist VARCHAR(255),
album VARCHAR(255),
genre VARCHAR(100),
release_year INTEGER,
cover_image_url TEXT,
youtube_url TEXT,
created_at TIMESTAMP DEFAULT NOW()
```

### song_lines — 가사 라인 (핵심 학습 단위)
```sql
id SERIAL PRIMARY KEY,
song_id INTEGER REFERENCES songs(id),
line_number INTEGER,
korean_text TEXT,
romanization TEXT,
translation JSONB,          -- {en: "...", es: "...", id: "..."}
ai_explanation TEXT,
emotional_context TEXT,
vocabulary JSONB,           -- [{korean, romanization, meaning, ...}]
embedding vector(1536)
```

### vocabulary — 단어 DB
```sql
id SERIAL PRIMARY KEY,
korean VARCHAR(100),
romanization VARCHAR(200),
meaning JSONB,              -- {en: "...", es: "..."}
part_of_speech VARCHAR(50),
formality_level VARCHAR(20), -- formal/informal/slang
usage_examples JSONB,
embedding vector(1536)
```

### users
```sql
id SERIAL PRIMARY KEY,
email VARCHAR(255) UNIQUE,
nickname VARCHAR(100),
target_language VARCHAR(10),
created_at TIMESTAMP DEFAULT NOW()
```

### user_progress — 학습 추적
```sql
id SERIAL PRIMARY KEY,
user_id INTEGER REFERENCES users(id),
song_id INTEGER REFERENCES songs(id),
learned_lines JSONB,        -- [line_id, ...]
streak_days INTEGER DEFAULT 0,
last_studied_at TIMESTAMP,
xp_points INTEGER DEFAULT 0
```

### user_vocabulary — 사용자 단어장
```sql
id SERIAL PRIMARY KEY,
user_id INTEGER REFERENCES users(id),
vocab_id INTEGER REFERENCES vocabulary(id),
mastery_level INTEGER DEFAULT 0, -- 0~5
last_reviewed_at TIMESTAMP,
is_favorite BOOLEAN DEFAULT FALSE
```

### pronunciation_sessions — 발음 연습 기록
```sql
id SERIAL PRIMARY KEY,
user_id INTEGER REFERENCES users(id),
song_line_id INTEGER REFERENCES song_lines(id),
audio_url TEXT,
transcript TEXT,
score FLOAT,
feedback JSONB,
created_at TIMESTAMP DEFAULT NOW()
```

---

## AI 서비스 추상화 레이어

```python
# ai_service.py 핵심 설계
class AIService:
    def __init__(self):
        self.primary = LMStudioClient()    # gemma / qwen via LM Studio
        self.fallback = OpenRouterClient() # OpenRouter (OpenAI 호환)

    async def complete(self, prompt, system, **kwargs) -> str:
        try:
            return await self.primary.complete(prompt, system, **kwargs)
        except (ConnectionError, TimeoutError):
            return await self.fallback.complete(prompt, system, **kwargs)
```

**LM Studio 연결:**
- 엔드포인트: `http://localhost:1234/v1` (OpenAI 호환)
- 모델: gemma-3-4b-it, qwen2.5-7b-instruct 등 GGUF
- 환경변수: `LM_STUDIO_BASE_URL`, `LM_STUDIO_MODEL`

**OpenRouter 폴백:**
- 엔드포인트: `https://openrouter.ai/api/v1`
- 환경변수: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`

---

## RAG 파이프라인

```
사용자 질문
    ↓
임베딩 생성 (sentence-transformers 로컬)
    ↓
pgvector 유사도 검색 (song_lines, vocabulary)
    ↓
상위 3개 컨텍스트 구성
    ↓
프롬프트 조합 → LM Studio → 응답 스트리밍
```

**AI 튜터 프롬프트 템플릿:**
```python
TUTOR_PROMPT = """
You are a warm Korean language tutor specializing in K-POP and K-culture.

Context (relevant expressions):
{rag_context}

Current lyrics line: {lyrics_line}
User language: {user_language}

User asks: {user_question}

Respond in {user_language}. Be warm, use K-POP examples, explain cultural nuance.
"""
```

---

## API 설계

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/songs` | 노래 목록 (페이징, 검색) |
| GET | `/api/songs/{id}` | 노래 상세 + 가사 |
| GET | `/api/songs/{id}/lines` | 가사 라인 목록 |
| POST | `/api/tutor/chat` | AI 튜터 채팅 (SSE 스트리밍) |
| POST | `/api/pronunciation/evaluate` | 발음 평가 |
| GET | `/api/learning/progress` | 학습 현황 |
| POST | `/api/learning/mark-learned` | 학습 완료 표시 |
| GET | `/api/learning/vocabulary` | 사용자 단어장 |

---

## 프론트엔드 주요 화면

1. **가사 학습** `/songs/[id]` — 카드 스와이프, 한→로마자→번역→AI설명
2. **AI 튜터** `/tutor` — 스트리밍 채팅, 질문 제안 칩
3. **발음 연습** `/practice` — 녹음→STT→점수→피드백
4. **대시보드** `/profile` — 스트릭, 학습 통계, 단어장

---

## Docker Compose

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: klyric_ai
      POSTGRES_USER: klyric
      POSTGRES_PASSWORD: klyric_dev
    ports: ["5432:5432"]
    volumes: ["./data/postgres:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

> LM Studio는 로컬에서 별도 실행 (localhost:1234)

---

## 구현 순서 (총 ~9일)

| Step | 내용 | 예상 일수 |
|------|------|----------|
| 1 | Docker 인프라 (PostgreSQL + Redis) + .env | 1일 |
| 2 | FastAPI 백엔드 + SQLAlchemy 모델 + 가사 API | 2일 |
| 3 | AI 서비스 추상화 + RAG + AI 튜터 API | 1일 |
| 4 | Whisper STT + 발음 평가 API | 1일 |
| 5 | Next.js 프론트엔드 4개 화면 | 3일 |
| 6 | 통합 테스트 + PWA + 모바일 최적화 | 1일 |

---

## 검증 방법

1. `docker-compose up` → PostgreSQL + Redis 기동 확인
2. LM Studio gemma 로드 → `/api/tutor/chat` 테스트
3. LM Studio 종료 → OpenRouter 폴백 자동 전환 확인
4. 가사 카드 스와이프 → AI 설명 로딩 확인
5. 발음 녹음 → Whisper STT → 점수 표시 확인
6. Chrome DevTools 모바일 시뮬레이션 PWA 동작 확인
