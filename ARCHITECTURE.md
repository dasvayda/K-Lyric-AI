# K-Lyric AI — Architecture

## Overview

K-Lyric AI는 K-POP 가사를 통해 한국어를 학습하는 웹 애플리케이션입니다. **프론트엔드-백엔드** 분리 구조로 운영되며, AI 튜터는 로컬 LiteRT 모델(Gemma)을 통해 제공됩니다.

```
┌─────────────────────────────────────┐
│   Frontend (Next.js) Port 3002      │
│  - React 19 + Zustand 상태관리      │
│  - TailwindCSS UI                   │
└────────────┬────────────────────────┘
             │ HTTP / REST API
             ▼
┌─────────────────────────────────────┐
│   Backend (FastAPI) Port 8001       │
│  - LiteRT Service (Gemma)           │
│  - Chat / Inference API             │
└─────────────────────────────────────┘
```

---

## Frontend (Next.js 16.2.6)

### 디렉토리 구조
```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   ├── globals.css         # Global styles
│   └── [...pages]/         # Additional pages
├── lib/
│   ├── ai.ts              # LM Studio / LiteRT 클라이언트
│   └── store.ts           # Zustand store 정의
├── data/
│   └── songs.json         # K-POP 가사 데이터
├── public/
├── .env.local             # 환경 변수 (백엔드 URL)
├── next.config.ts
├── tsconfig.json
└── package.json
```

### 주요 스택
- **Next.js 16**: App Router 기반 SSR/SSG
- **React 19**: UI 렌더링
- **Zustand 5**: 가볍고 간단한 상태관리 (학습 진도, 즐겨찾기, 스트릭)
- **TailwindCSS 4**: 유틸리티 기반 스타일
- **TypeScript**: 타입 안전성

### 환경 변수 (.env.local)
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
NEXT_PUBLIC_LM_STUDIO_URL=http://localhost:1234/v1  # LM Studio (대체 옵션)
```

---

## Backend (FastAPI + Python)

### 디렉토리 구조
```
backend/
├── main.py                    # FastAPI 앱 진입점
├── services/
│   └── litert_service.py     # LiteRT 추론 엔진
├── requirements.txt           # Python 의존성
├── .env                      # 환경 설정
└── .env.example
```

### 주요 스택
- **FastAPI**: 비동기 REST API 프레임워크
- **LiteRT (MediaPipe)**: 로컬 AI 모델 추론
  - 모델: Gemma (DocuDog 번들)
  - CPU/GPU 최적화
- **Pydantic**: 요청/응답 검증

### Core Endpoints

#### 1. Chat Completion
```
POST /chat
Content-Type: application/json

{
  "prompt": "한국어 배우기",
  "system": "너는 한국어 튜터다"
}

Response:
{
  "response": "반갑습니다! 함께 배워봅시다..."
}
```

#### 2. Health Check
```
GET /health
```

---

## Data Flow

### 1. 사용자가 AI 튜터에 질문
```
Frontend (user input)
    ↓ POST /chat (ChatMessage)
Backend (litert_service)
    ↓ LiteRT inference
Backend
    ↓ response
Frontend (Zustand 상태 업데이트)
    ↓ re-render
UI 업데이트
```

### 2. 가사 학습 (로컬 데이터)
```
Frontend loads songs.json
    ↓
Zustand store (현재 곡, 단어장, 진도)
    ↓
UI 렌더링 (카드 스와이프, AI 설명)
```

---

## Communication

### CORS 설정
- **Origin**: `http://localhost:3002`, `http://localhost:3001`, `http://localhost:3000`
- **Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Headers**: 모든 헤더 허용

### Port 할당
| 서비스 | Port | 설명 |
|--------|------|------|
| Frontend | 3002 | Next.js dev server |
| Backend | 8001 | FastAPI server |
| LM Studio | 1234 | 대체 AI 추론 (필요시) |

---

## Phase 1 Status (완료)

- ✅ 프론트엔드: 5개 페이지 기본 UI
- ✅ 백엔드: FastAPI + LiteRT 통합
- ✅ Zustand: 상태 관리 기본 구조
- ⏳ API 통신: 기본 엔드포인트

---

## Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
```

### Backend (.env)
```env
LITERT_MODEL_PATH=./models/gemma  # (예시)
BACKEND_PORT=8001
```

---

## 향후 확장

1. **인증**: JWT 토큰 기반 사용자 구분
2. **데이터 저장**: PostgreSQL + Supabase
3. **발음 인식**: Web Speech API + 백엔드 평가
4. **실시간 스트리밍**: WebSocket 기반 스트리밍 응답
5. **PWA**: 오프라인 학습 지원

---

## 로컬 개발 실행

### 1. 백엔드 시작
```bash
cd backend
pip install -r requirements.txt
python main.py  # uvicorn main:app --reload --port 8001
```

### 2. 프론트엔드 시작
```bash
cd frontend
npm install
npm run dev  # http://localhost:3002
```

### 3. 테스트
```bash
curl http://localhost:8001/health
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"안녕하세요"}'
```
