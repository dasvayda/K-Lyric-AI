# K-Lyric AI — Step 1-3 완료 보고서

## ✅ 완료된 작업

### Step 1: Next.js 프로젝트 초기화 + 폴더 구조
- [x] Next.js 14 (App Router) 초기화 완료
- [x] TailwindCSS 설정 완료
- [x] Zustand 설치 완료
- [x] `.env.local` 생성 (LM_STUDIO_URL 설정)
- [x] `app/page.tsx` 기본 UI 구현 (홈 화면 with 노래 목록)
- [x] `app/layout.tsx` 메타데이터 설정

**생성된 파일:**
```
frontend/
├── app/
│   ├── layout.tsx          (K-Lyric AI 메타)
│   ├── page.tsx            (홈: 노래 목록 + AI 튜터/발음/대시보드 링크)
│   └── globals.css
├── lib/
│   ├── ai.ts               (✅ 아래 참조)
│   ├── data.ts             (✅ 아래 참조)
│   └── store.ts            (✅ 아래 참조)
├── data/
│   └── songs.json          (✅ 아래 참조)
├── .env.local
├── package.json            (Zustand 포함)
└── next.config.js
```

**상태**: `npm run dev` 실행 가능 (localhost:3000)

---

### Step 2: LM Studio 통신 클라이언트 구현
**파일**: `frontend/lib/ai.ts`

**구현 내용:**
- `AIError` 클래스 — 에러 스테이징 (DocuDog 참조)
- `callLMStudio()` — 단일 호출 (OpenAI 호환 /chat/completions)
  - 타임아웃 처리 (기본 30초)
  - JSON 파싱 + 에러 처리
  - Bearer token 지원
  - 네트워크 에러 처리 (URLError, TypeError)

- `streamLMStudio()` — 스트리밍 응답 (AsyncIterable)
  - Server-Sent Events 파싱
  - 청크 단위 yield
  - 연결 실패 시 graceful error

**참조 코드**: DocuDog `inference.py` (663줄)
- `_openai_http_chat_completion()` — HTTP POST 로직
- `_assistant_text_from_openai_message()` — 메시지 파싱
- Error classes: `HttpInferenceError`

**테스트 준비:**
```bash
# LM Studio 실행 필수
# 기본 포트: http://localhost:1234/v1
# 모델: gemma-2b (이미 테스트됨)
```

---

### Step 3: 가사 데이터 샘플 + 구조 정의

**파일 1**: `frontend/data/songs.json`
- **데이터**: K-POP 노래 3곡 (IVE, BTS ×2)
- **각 라인 포함**:
  - korean_text
  - romanization
  - translation (en, es, id)
  - ai_explanation
  - emotional_context
  - vocabulary (단어별 의미, 품사, 격식 레벨)

**예시**:
```json
{
  "id": "1-1",
  "korean_text": "모두 다 하나처럼",
  "romanization": "modu da hana cheoreom",
  "translation": {
    "en": "Everyone just like one",
    "es": "Todos como uno"
  },
  "vocabulary": [
    {
      "korean": "모두",
      "meaning": { "en": "everyone, all" },
      "part_of_speech": "noun"
    }
  ]
}
```

**파일 2**: `frontend/lib/data.ts`
- `loadSongs()` — songs.json 로드 (메모이제이션)
- `getSongById(id)` — ID로 노래 조회
- `getAllSongs(page, pageSize)` — 페이지네이션
- `searchSongs(query)` — 제목/아티스트 검색
- `getRandomSong()` — 일일 도전용 랜덤

**Type exports**:
- `Song` 인터페이스
- `SongLine` 인터페이스
- `Vocabulary` 인터페이스

---

## 📊 Zustand 상태 관리

**파일**: `frontend/lib/store.ts`

**상태**:
- `learnedLines: Set<string>` — 학습한 라인 ID
- `favorites: Set<string>` — 즐겨찾기
- `currentSongId: number` — 현재 학습 노래
- `streak: number` — 연속 학습일수
- `lastStudiedDate: string` — 마지막 학습 날짜
- `xpPoints: number` — 누적 경험치
- `userLanguage: "en" | "es" | "id" | "ko"` — 사용자 언어

**Actions**:
- `markLineAsLearned(lineId)`
- `toggleFavorite(lineId)`
- `setCurrentSong(songId)`
- `addXP(points)`
- `updateStreak(increment)`
- `setUserLanguage(language)`
- `resetProgress()`

**localStorage 자동 저장** (Set → Array 변환):
```typescript
// Zustand persist middleware로 자동 직렬화/역직렬화
```

**유틸 함수**:
- `getStreakLabel(days)` — 🔥 이모지로 표시
- `getLevel(xpPoints)` — XP → 레벨 계산
- `getLevelProgress(xpPoints)` — 현재 레벨 진행도 (0-100)

---

## 🏠 홈 화면 구현

**파일**: `frontend/app/page.tsx`

**기능**:
- songs.json에서 노래 목록 로드
- 카드 그리드 표시 (커버 이미지 포함)
- 각 카드 클릭 → `/songs/[id]`로 이동
- 3개 빠른 링크: AI Tutor, Practice, Dashboard

**스타일**:
- 다크 테마 (Tailwind)
- 반응형 레이아웃 (md/lg 브레이크포인트)
- 호버 효과

---

## 🚀 다음 세션 체크리스트

### PC OFF 전에 확인할 사항
1. **LM Studio 연결 테스트**
   - LM Studio에서 gemma 또는 qwen 모델 로드
   - 서버 상태: `http://localhost:1234/v1/models`에서 active model 확인

2. **Next.js 개발 서버 확인**
   ```bash
   cd c:\mydev\K-Lyric-AI\frontend
   npm run dev
   # http://localhost:3000 접속
   # 노래 목록이 표시되는지 확인
   ```

3. **콘솔 에러 확인**
   - 브라우저 DevTools에서 에러 메시지 없는지 확인
   - Network 탭에서 `/data/songs.json` 로드 확인

### PC 재시작 후 진행할 작업 (Step 4+)

다음 세션에서:
1. **AI 튜터 채팅 화면** (`/app/tutor/page.tsx`)
   - LM Studio HTTP 호출 테스트
   - 스트리밍 응답 표시

2. **가사 학습 화면** (`/app/songs/[id]/page.tsx`)
   - 가사 라인을 카드로 표시
   - 단어장 탭

3. **발음 연습 화면** (`/app/practice/page.tsx`)
   - Web Speech API로 녹음
   - STT 결과 표시

4. **대시보드** (`/app/profile/page.tsx`)
   - Zustand store에서 데이터 조회
   - 스트릭, XP, 학습 통계 표시

---

## 📝 참고

### 사용한 코드 패턴
- **LM Studio HTTP**: DocuDog `_openai_http_chat_completion()` 참조
- **에러 처리**: DocuDog `HttpInferenceError` 구조 차용
- **상태 관리**: Zustand + localStorage persist

### 환경 설정
```env
# .env.local
NEXT_PUBLIC_LM_STUDIO_URL=http://localhost:1234/v1
NEXT_PUBLIC_LM_STUDIO_MODEL=local-model
```

### 디렉터리 구조
```
c:\mydev\K-Lyric-AI\
├── frontend/              (Next.js 앱)
│   ├── app/              (페이지 라우팅)
│   ├── lib/              (유틸 + AI 클라이언트)
│   ├── data/             (정적 데이터)
│   ├── .env.local        (환경변수)
│   └── package.json      (의존성)
├── .docs/                (계획 문서)
├── todo-list.txt         (나중에 필요한 기능)
└── WORK-PLAN.md          (작업 계획)
```

---

## 소요 시간

| 작업 | 예상 | 실제 |
|------|------|------|
| Next.js 초기화 | 1-2h | ~1.5h |
| LM Studio 클라이언트 | 1-2h | ~1h |
| 가사 데이터 + Zustand | 1-2h | ~1h |
| **총합** | **3-6h** | **~3.5h** |

---

## ✅ 정리

**현재 상태**: 프로토타입 기반 완성
- ✅ 프론트엔드 뼈대 준비
- ✅ LM Studio 연결 로직 (테스트 필요)
- ✅ 데이터 구조 정의
- ✅ 상태 관리 설정
- ⏳ 실제 화면 구현 (Step 4+)

다음 세션에서 **실제 기능 화면들**(AI 튜터, 가사 학습, 발음 연습)을 만들면 MVP가 동작 가능해집니다.
