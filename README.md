# Backend API

FastAPI backend. Deploying to **Render**.

---

## Render 배포 시 필수 환경변수

Render Dashboard → Your Service → **Environment** 탭에서 설정.

| 변수명 | 필수 | 설명 | 예시 |
|---|---|---|---|
| `DATABASE_URL` | **필수** | PostgreSQL 연결 문자열 | `postgresql://user:pass@host/dbname` |
| `REDIS_URL` | 선택 | Redis 캐시 URL (없으면 캐시 비활성) | `redis://default:pass@host:6379` |
| `LLM_PROVIDER` | 선택 | AI 공급자 선택 | `gemini` (기본값) 또는 `openai` |
| `GEMINI_API_KEY` | LLM 사용 시 필수 | Google Gemini API 키 | `AIza...` |
| `GEMINI_MODEL` | 선택 | Gemini 모델명 | `gemini-2.0-flash` (기본값) |
| `OPENAI_API_KEY` | `openai` 선택 시 필수 | OpenAI API 키 | `sk-...` |
| `OPENAI_MODEL` | 선택 | OpenAI 모델명 | `gpt-4o-mini` (기본값) |
| `GOOGLE_MAPS_API_KEY` | 선택 | 출생지 좌표/타임존 자동 조회용 | `AIza...` |

> `DATABASE_URL`이 `postgres://`로 시작하면 자동으로 `postgresql://`로 변환됩니다.

---

## Render 배포 절차

1. Render → **New Web Service** → GitHub 레포 연결
2. **Runtime**: Docker (Dockerfile 사용)
3. **Start Command**: 이미 Dockerfile에 포함 (`uvicorn main:app --host 0.0.0.0 --port 8000`)
4. **Environment** 탭에서 위 환경변수 입력
5. PostgreSQL이 필요하면 Render → **New PostgreSQL** 생성 후 `DATABASE_URL` 복사

---

## API 엔드포인트 (Flutter 연동용)

### `POST /login`

Firebase 로그인 후 유저 등록/갱신.

```json
Request: { "uid": "firebase_uid", "email": "user@example.com", "provider": "google" }
Response: { "status": "ok", "uid": "firebase_uid" }
```

---

### `POST /saju`

사주 계산 + 선택적 AI 분석. **핵심 엔드포인트.**

```json
Request:
{
  "birth_date": "1990-01-15",
  "birth_time": "14:30",
  "timezone": "Asia/Seoul",
  "longitude": 127.0,
  "latitude": 37.5,
  "birth_place": "Paris",
  "include_analysis": false,
  "theme": "general",
  "user_id": "firebase_uid"
}

Response:
{
  "record_id": 42,
  "lunar": { "year": 1989, "month": 12, "day": 20, "isLeapMonth": false },
  "saju": { "year": "己巳", "month": "癸丑", "day": "甲子", "time": "壬申" },
  "elements": { "Wood": 2, "Fire": 1, "Earth": 3, "Metal": 1, "Water": 1 },
  "analysis": "..."
}
```

---

### `GET /fortune/{period}/{record_id}`

기간별 에너지 분석. `/saju`에서 받은 `record_id` 사용.

- `period` 값: `daily` | `weekly` | `monthly` | `yearly` | `life`

**⚠️ 라이프스타일 언어 요구사항**  
Flutter 앱에서 "운세" 느낌을 완전히 제거합니다. 응답 필드를 아래 기준으로 조정:

| 기존 | 변경 |
|---|---|
| `insight`: "오늘 재물운이 강하다" | `insight`: "Your productive energy flows strongly today" |
| `period`: "Today's Fortune" | `period`: "Today's Rhythm" |

추가 응답 필드 (Flutter `SajuModel.rhythmKeyword`, `yearTheme` 등에서 사용):

```json
{
  "period": "Today's Rhythm",
  "mode": "EXPRESSION",
  "score": 83,
  "insight": "Your creative output flows naturally today. A good day to start new projects.",
  "rhythm_keyword": "Creative",
  "year_theme": "2026 Pattern",
  "year_description": "A year of grounded expansion. Your Wood energy supports steady growth.",
  "image_keyword": "creative studio, warm amber light, textured surface, cinematic, 8k"
}
```

- `rhythm_keyword`: 오늘의 리듬 단어 (`"Creative"`, `"Reflective"`, `"Steady"`, `"Productive"`, `"Restorative"` 등)
- `year_theme`: 연간 테마 한 줄
- `year_description`: 연간 설명 2–3문장 (운세 언어 금지)

---

### `GET /history/{user_id}`

유저의 최근 10개 기록 조회.

```json
Response: [ { "record_id": 42, "created_at": "2026-04-16T10:00:00", "saju": {...}, ... } ]
```

---

## Feed API (신규 — 라이프스타일 피드)

커뮤니티 피드 기능. 유저가 자신의 엘리멘털 패턴 카드를 공개 피드에 공유.  
**운세/점술 언어 완전 배제 — "패턴", "리듬", "에너지" 용어만 사용.**

---

### `GET /feed`

공개 피드 목록 (최신순).

**Query Parameters:**
- `limit` (int, 기본 20)
- `offset` (int, 기본 0)

**Response:**
```json
[
  {
    "post_id": 1,
    "record_id": 42,
    "display_name": "Voyager",
    "archetype": "The Voyager",
    "dominant": "Water",
    "rhythm": "Reflective",
    "year_theme": "2026 Flow",
    "elements": { "Wood": 1, "Fire": 1, "Earth": 2, "Metal": 1, "Water": 3 },
    "caption": null,
    "created_at": "2026-04-16T08:00:00"
  }
]
```

**신규 DB 테이블:**
```sql
CREATE TABLE feed_posts (
    id          SERIAL PRIMARY KEY,
    record_id   INTEGER NOT NULL REFERENCES saju_records(id),
    caption     TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (record_id)
);
```

---

### `POST /feed`

피드에 패턴 카드 공유.

**Request:**
```json
{ "record_id": 42, "caption": "My natural rhythm today" }
```

**Response:**
```json
{ "status": "ok", "post_id": 1 }
```

**처리 로직:**
1. `record_id`로 사주 레코드 조회
2. `archetype`, `dominant_element`, `rhythm_keyword`, `year_theme` 추출
3. 동일 `record_id` 중복 포스팅 방지 (upsert)
4. `display_name`: 유저 UID → `users` 테이블에서 `nickname` 조회, 없으면 archetype 이름 사용

---

### `GET /feed/{post_id}`

개별 피드 포스트 단건 조회. 응답 구조는 `GET /feed` 아이템과 동일.

---

## 라이프스타일 AI 프롬프트 가이드

`/saju`의 `analysis` 및 `/fortune`의 `insight` 생성 시 아래 규칙 준수.

**금지 표현:**
- "운이 좋다/나쁘다", "재물운", "관운", "연애운"
- "destiny", "fate", "fortune", "luck", "horoscope"
- "당신의 운명은", "조심하세요"

**권장 표현:**
- "your natural rhythm", "elemental tendency", "energy pattern"
- "this period supports", "your creative flow", "a grounded phase"
- "Wood energy suggests expansion", "Water energy invites reflection"

**백엔드 시스템 메시지 예시:**
```text
You are a lifestyle and personality coach, NOT a fortune teller.
Respond with elemental energy patterns and natural tendencies only.
Do NOT use fortune-telling, horoscope, or destiny language.
Frame everything as rhythms, cycles, and natural inclinations.
Tone: warm, grounded, modern. Language: English.
```

---

## 로컬 개발

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

`.env`:
```env
DATABASE_URL=postgresql://...
GEMINI_API_KEY=AIza...
GOOGLE_MAPS_API_KEY=AIza...
```
