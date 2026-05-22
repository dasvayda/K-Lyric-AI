# K-Lyric AI — 작업 계획 (단계별)

## 현재 상태
- DocuDog ARCHITECTURE.md 검토 완료 (LiteRT-LM 기반)
- DocuDog inference.py LM Studio HTTP 통신 로직 확인 완료
- 참조 가능: `_openai_http_chat_completion()` 함수 (663줄)

## 선행 작업 (PC OFF 전까지만)

### ✅ Step 1: Next.js 프로젝트 초기화 + 기본 폴더 구조
**목표**: 프로젝트 뼈대 완성, `npm run dev` 실행 가능 상태
**파일 생성**:
- `frontend/package.json` (Next.js 14, TailwindCSS, Zustand)
- `frontend/next.config.js` (PWA)
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx` (홈)
- `frontend/.env.local` (LM_STUDIO_URL)

**소요 시간**: 1-2시간

---

### ⏳ Step 2: LM Studio 통신 클라이언트 구현
**목표**: LM Studio와 OpenAI 호환 API로 통신하는 로직 구현
**참조**: DocuDog `_openai_http_chat_completion()` (inference.py 663줄)

**파일 생성**:
- `frontend/lib/ai.ts`
  - `AIClient` 클래스 (LM Studio HTTP 호출)
  - `callLMStudio(prompt, system, options)` 함수
  - Error handling (timeout, connection)

**구체적 로직**:
```typescript
// frontend/lib/ai.ts
const fetch(`http://localhost:1234/v1/chat/completions`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    model: "local-model",
    messages: [
      { role: "system", content: system },
      { role: "user", content: prompt }
    ],
    temperature: 0.7,
    max_tokens: 500
  })
})
```

**소요 시간**: 1-2시간

---

### ⏳ Step 3: 가사 데이터 샘플 + JSON 구조 정의
**목표**: K-POP 노래 3-5곡의 가사 데이터 정의
**파일 생성**:
- `frontend/data/songs.json` (K-POP 노래 데이터)
  - 각 라인: korean_text, romanization, translation, vocabulary, ai_explanation

**샘플 데이터**:
```json
{
  "songs": [
    {
      "id": 1,
      "title": "좋아하는 마음",
      "artist": "IVE",
      "lines": [
        {
          "id": "1-1",
          "korean_text": "보고 싶다",
          "romanization": "bogo sipda",
          "translation": { "en": "I miss you", "es": "Te echo de menos" },
          "vocabulary": [...],
          "ai_explanation": "..."
        }
      ]
    }
  ]
}
```

**소요 시간**: 1-2시간 (K-POP 가사 수집 + 번역 + 설명)

---

## 이 이후 작업 (PC OFF 후 다시 시작)

### Step 4: Zustand 상태 관리 설정
- 사용자 학습 진행도
- 즐겨찾기
- 스트릭 계산

### Step 5: 가사 학습 화면 UI
- 카드 스와이프 컴포넌트

### Step 6: AI 튜터 채팅 화면
- LM Studio 연결 테스트
- 스트리밍 응답

### Step 7: 발음 연습 화면
- Web Speech API STT

### Step 8: 학습 대시보드
- 통계 표시

### Step 9: 통합 테스트 + PWA 설정

---

## 참고: DocuDog에서 참조할 코드

**File**: `C:\mydev\DocuDog\docudog\inference.py`

**핵심 함수들**:
- `_openai_http_chat_completion()` (663줄) — OpenAI 호환 HTTP POST
  - JSON 인코딩
  - Bearer token (필요시)
  - Error handling (HTTPError, URLError, JSONDecodeError)
  - Response parsing: `choices[0].message.content`

- `_assistant_text_from_openai_message()` (105줄) — message 파싱
  - content 필드 추출
  - reasoning_content 폴백

**에러 클래스**:
- `HttpInferenceError` (44줄) — HTTP 실패 정보 보존

---

## 환경 설정

**파일**: `frontend/.env.local`
```env
NEXT_PUBLIC_LM_STUDIO_URL=http://localhost:1234/v1
NEXT_PUBLIC_LM_STUDIO_MODEL=local-model
```

---

## 예상 일정

| 작업 | 예상 시간 | 누적 |
|------|----------|------|
| Step 1: Next.js 초기화 | 1-2h | 1-2h |
| Step 2: LM Studio 클라이언트 | 1-2h | 2-4h |
| Step 3: 가사 데이터 샘플 | 1-2h | 3-6h |
| **현재 PC OFF까지 총** | **3-6시간** | **3-6h** |

---

## 다음 세션 체크리스트

- [ ] `npm run dev` 실행 가능?
- [ ] LM Studio localhost:1234 응답 확인?
- [ ] 가사 데이터 JSON 로드 확인?

모두 확인되면 Step 4부터 진행.
