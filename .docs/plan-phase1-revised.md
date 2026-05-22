# K-Lyric AI — Phase 1 MVP 구현 계획 (옵션 1: 서버 없음)

## Context

`phase1.txt` 스펙 기반 K-POP 가사로 한국어를 학습하는 모바일 퍼스트 플랫폼.

**최적화된 설정 (프론트엔드 중심):**
- **범위**: Phase 1 MVP만 구현
- **AI**: LM Studio(gemma/qwen SLLM) 로컬 실행
- **벡터 DB**: Chroma (로컬 파일 기반, SQLite) — 서버 불필요
- **구조**: 순수 프론트엔드 + 로컬 LLM (서버 없음)

---

## 폴더 구조 (간소화)

```
c:\mydev\K-Lyric-AI\
├── frontend/                    # Next.js 14 App Router (전부)
│   ├── app/
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
│   │   ├── ai.ts               # LM Studio API 클라이언트
│   │   ├── embeddings.ts       # sentence-transformers 래퍼
│   │   ├── rag.ts              # Chroma RAG 로직
│   │   ├── store.ts            # Zustand 상태 관리 (사용자 진행도)
│   │   └── data.ts             # 가사 데이터 (JSON 또는 CSV)
│   ├── data/
│   │   ├── songs.json          # K-POP 노래 데이터
│   │   └── embeddings.json     # 미리 생성된 임베딩 캐시
│   ├── public/                 # PWA manifest, icons
│   ├── next.config.js          # PWA 설정
│   ├── tailwind.config.js
│   └── package.json
│
├── .docs/                       # 임시 계획 문서
├── todo-list.txt               # 나중에 필요한 기능
└── .env.example                # 환경 설정 (LM_STUDIO_URL 등)
```

---

## 기술 스택

| 레이어 | 도구 |
|--------|------|
| **프론트엔드** | Next.js 14 (App Router), React, TailwindCSS |
| **상태 관리** | Zustand (사용자 학습 진행도, 즐겨찾기) |
| **LLM 추론** | LM Studio (localhost:1234) |
| **임베딩** | sentence-transformers (로컬 Python 또는 ONNX.js) |
| **벡터 DB** | Chroma (로컬 파일 기반) 또는 FAISS |
| **STT** | Web Speech API 또는 Whisper.cpp (로컬) |
| **오디오** | WebAudio API |
| **PWA** | next-pwa 패키지 |

---

## 데이터 구조

### songs.json (프로젝트 내 정적 데이터)

```json
{
  "songs": [
    {
      "id": 1,
      "title": "좋아하는 마음",
      "artist": "IVE",
      "album": "I AM",
      "genre": "K-POP",
      "release_year": 2022,
      "cover_image_url": "https://...",
      "youtube_url": "https://youtu.be/...",
      "lines": [
        {
          "id": "1-1",
          "line_number": 1,
          "korean_text": "보고 싶다",
          "romanization": "bogo sipda",
          "translation": {
            "en": "I miss you",
            "es": "Te echo de menos",
            "id": "Aku merindukanmu"
          },
          "ai_explanation": "This expression is commonly used to express emotional longing.",
          "emotional_context": "Longing, yearning, affection",
          "vocabulary": [
            {
              "korean": "보고",
              "romanization": "bogo",
              "meaning": { "en": "to see", "es": "ver" },
              "part_of_speech": "verb",
              "formality_level": "informal"
            },
            {
              "korean": "싶다",
              "romanization": "sipda",
              "meaning": { "en": "want to", "es": "quiero" },
              "part_of_speech": "auxiliary verb",
              "formality_level": "informal"
            }
          ]
        }
      ]
    }
  ]
}
```

### Zustand Store (사용자 상태)

```typescript
// lib/store.ts
interface UserProgress {
  learnedLines: Set<string>;
  favorites: Set<string>;
  streak: number;
  lastStudiedDate: string;
  xpPoints: number;
}

const useStore = create<UserProgress>((set) => ({
  learnedLines: new Set(),
  favorites: new Set(),
  streak: 0,
  lastStudiedDate: new Date().toISOString(),
  xpPoints: 0,
  // ... actions
}));
```

---

## LM Studio 연결

### 클라이언트 코드

```typescript
// lib/ai.ts
export async function completeLMStudio(
  prompt: string,
  system: string,
  stream: boolean = false
): Promise<string | AsyncIterable<string>> {
  const baseURL = process.env.NEXT_PUBLIC_LM_STUDIO_URL || 
                   "http://localhost:1234/v1";
  
  const response = await fetch(`${baseURL}/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "local-model", // LM Studio 자동 감지
      messages: [
        { role: "system", content: system },
        { role: "user", content: prompt }
      ],
      stream: stream,
      temperature: 0.7,
      max_tokens: 500
    })
  });

  if (stream) {
    return response.body?.getReader(); // SSE 스트리밍
  }
  
  const data = await response.json();
  return data.choices[0].message.content;
}
```

---

## RAG 파이프라인 (로컬)

### Chroma 또는 FAISS 사용

```typescript
// lib/rag.ts
import { ChromaClient } from "chroma-db"; // 또는 FAISS
import { pipeline } from "@xenova/transformers"; // ONNX.js 임베딩

const embedder = await pipeline(
  "feature-extraction",
  "Xenova/all-MiniLM-L6-v2" // 로컬 임베딩 모델
);

async function embedAndStore(lines: SongLine[]) {
  for (const line of lines) {
    const embedding = await embedder(line.korean_text);
    await chroma.add({
      ids: [line.id],
      documents: [line.korean_text],
      metadatas: [{ 
        translation: line.translation,
        explanation: line.ai_explanation 
      }],
      embeddings: [embedding]
    });
  }
}

async function retrieveContext(userQuestion: string) {
  const questionEmbedding = await embedder(userQuestion);
  const results = await chroma.query({
    query_embeddings: [questionEmbedding],
    n_results: 3
  });
  return results;
}
```

---

## API 설계 (프론트엔드 내부)

실제 API 없음. 모든 로직이 프론트엔드 컴포넌트 또는 유틸에서 실행:

| 기능 | 구현 위치 |
|------|----------|
| 가사 로드 | `app/songs/[id]/page.tsx` → `lib/data.ts` |
| AI 튜터 | `app/tutor/page.tsx` → `lib/ai.ts` + `lib/rag.ts` |
| 발음 평가 | `app/practice/page.tsx` → `lib/ai.ts` + Web Speech API |
| 학습 추적 | `lib/store.ts` (Zustand) + localStorage |

---

## 프론트엔드 주요 화면

### 1. 가사 학습 화면 (`/songs/[id]`)
- 카드 스와이프형 가사 라인 표시
- 각 카드: 한국어 → 로마자 → 번역 → AI 설명
- "더 알아보기" → AI 튜터 채팅 연결
- 단어 탭으로 어휘 추출 표시
- 하트 아이콘으로 즐겨찾기 (Zustand에 저장)

### 2. AI 튜터 채팅 (`/tutor`)
- 현재 학습 중인 가사 컨텍스트 유지
- LM Studio에 직접 요청 (SSE 스트리밍)
- RAG로 관련 가사/단어 검색 후 컨텍스트에 포함
- 질문 제안 칩: "격식체인가요?", "실생활에서 쓰나요?" 등

### 3. 발음 연습 (`/practice`)
- 가사 라인 표시 → 녹음 버튼 → Web Speech API STT → 점수
- 간단한 점수: 텍스트 유사도 (Levenshtein distance)
- 피드백: "좋아요!", "다시 시도해보세요" 정도

### 4. 학습 대시보드 (`/profile`)
- 스트릭 캘린더 (로컬스토리지에서 계산)
- 학습한 단어 수 / 노래 수 (Zustand에서 조회)
- 즐겨찾기 표현 모음

---

## 구현 순서 (총 ~4-5일)

| Step | 내용 | 예상 일수 |
|------|------|----------|
| 1 | Next.js 프로젝트 초기화 + 데이터 구조 정의 | 0.5일 |
| 2 | LM Studio 클라이언트 + 프롬프트 템플릿 | 0.5일 |
| 3 | Chroma/FAISS 임베딩 + RAG 파이프라인 | 1일 |
| 4 | 가사 학습 화면 + 컴포넌트 | 1일 |
| 5 | AI 튜터 채팅 화면 + 스트리밍 | 0.5일 |
| 6 | 발음 연습 화면 + STT | 0.5일 |
| 7 | 학습 대시보드 + Zustand 상태 관리 | 0.5일 |
| 8 | PWA 설정 + 모바일 최적화 + 테스트 | 1일 |

---

## 환경 설정 (.env.example)

```env
# LM Studio 로컬 실행 (기본값)
NEXT_PUBLIC_LM_STUDIO_URL=http://localhost:1234/v1
NEXT_PUBLIC_LM_STUDIO_MODEL=local-model

# 선택: OpenRouter 폴백 (나중에 추가)
# NEXT_PUBLIC_OPENROUTER_API_KEY=sk-...
# NEXT_PUBLIC_OPENROUTER_MODEL=google/gemma-3-4b-it:free
```

---

## 검증 방법

1. LM Studio에서 gemma 또는 qwen 모델 로드
   ```bash
   LM Studio를 열고 모델 로드 후 Server 시작 (localhost:1234)
   ```

2. Next.js 개발 서버 시작
   ```bash
   npm run dev
   ```

3. 브라우저에서 http://localhost:3000 접속

4. 각 화면 검증:
   - `/songs/1` → 가사 라인 표시, "더 알아보기" 클릭 → AI 설명 로딩
   - `/tutor` → 질문 입력 → LM Studio에서 응답 (스트리밍)
   - `/practice` → 녹음 → STT → 점수 표시
   - `/profile` → 스트릭, 학습 통계 표시

5. 모바일 Chrome DevTools (iPhone 시뮬레이션)에서 PWA 동작 확인
   - 설치 가능 여부
   - 오프라인 캐싱 (특정 페이지)

---

## 향후 마이그레이션 (Phase 2+)

프론트엔드 로컬 구조에서 서버 기반으로 전환할 때:
- `lib/ai.ts` → FastAPI 엔드포인트로 변경
- `lib/rag.ts` → PostgreSQL + pgvector 쿼리로 변경
- Zustand → 서버 동기화 추가 (React Query)
- 자세한 내용은 `todo-list.txt` 참조
