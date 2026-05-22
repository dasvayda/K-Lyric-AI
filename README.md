# K-Lyric AI

K-POP 가사로 배우는 한국어 학습 웹 앱

## 🎯 핵심 컨셉

- **K-POP 가사 기반 학습**: 실제 노래 가사를 통해 자연스러운 한국어 습득
- **AI 튜터**: LiteRT(Gemma) 기반 개인 맞춤형 설명
- **발음 + 문법 + 문화**: 단어, 표현, 문화적 배경을 통합 학습

## 🏗️ 구조

```
┌─ Frontend (Next.js 3002)
│  └─ React 19 + Zustand + TailwindCSS
└─ Backend (FastAPI 8001)
   └─ LiteRT(Gemma) 로컬 추론
```

자세한 아키텍처는 [ARCHITECTURE.md](ARCHITECTURE.md) 참고

## 🚀 로컬 실행

### 백엔드
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 프론트엔드
```bash
cd frontend
npm install
npm run dev
```

접속: http://localhost:3002

## 📋 현재 상태

- ✅ Phase 1: 기본 UI + 아키텍처 구성 완료
- ⏳ Phase 2: API 통신 + 데이터 연동
- ⏳ Phase 3: 실제 학습 기능 구현

## 🛠️ 기술 스택

| 계층 | 기술 |
|------|------|
| Frontend | Next.js 16, React 19, Zustand, TailwindCSS |
| Backend | FastAPI, Python |
| AI | LiteRT (MediaPipe) - Gemma 모델 |
| Styling | TailwindCSS 4 |

## 📝 라이센스

MIT
