# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

삼성역 맛집 투표 사이트. 사용자가 가게를 여러 곳 고르고 닉네임·한줄평을 남기면 Supabase `votes` 테이블에 저장하고, 결과 페이지에서 순위·한줄평·CSV를 보여준다. Python 표준 라이브러리만 쓰며 빌드·린트·테스트 도구는 없다.

## Commands

```bash
python -X utf8 server.py          # http://localhost:8000/ (투표), /result (결과)
```

- 테스트(리팩터링 안전망): `python -X utf8 -m unittest discover -s tests -v`. 하나만: `python -X utf8 -m unittest discover -s tests -k test_export_csv`.
  - `tests/fake_supabase.py`가 가짜 PostgREST를 띄우고, `tests/run_server.py`가 `socket.bind`를 가로채 포트 8000 대신 빈 포트로 `server.py`를 별도 프로세스로 실행한다. 실제 Supabase·`.env.local`은 쓰지 않고, 내부 구현에 기대지 않아 리팩터링 뒤에도 그대로 돌린다.
  - 다른 구현을 검사하려면 `SURVEY_SERVER=<server.py 경로>`.
  - 테스트는 현재 동작을 그대로 기록한 것이다. 동작을 일부러 바꾸려면 테스트를 먼저 고친다.
- 상위 폴더의 `.claude/launch.json`에 `survey-server` 프리뷰 설정이 있다 (포트 8000).
- `.env.local`(`vercel env pull`로 받은 파일)에서 `SUPABASE_URL`과 `SUPABASE_SECRET_KEY`(없으면 `SUPABASE_SERVICE_ROLE_KEY`)를 읽는다. 없으면 시작 시 `KeyError`로 죽는다.
- DB 스키마는 `supabase/migrations/`에 있다. RLS만 켜고 정책이 없으므로 브라우저에서 직접 접근할 수 없고 서버의 secret key로만 읽고 쓴다.

## Architecture

- `public/index.html`, `public/result.html`: 정적 페이지. 동기 XHR로 API를 호출한다.
- API (모두 `server.py`):
  - `GET /api/restaurants` — 하드코딩된 가게 목록
  - `POST /api/votes` — `{picks, nickname(≤20자), comment(≤200자)}`. 목록에 없는 id는 버리고, 하나도 안 남으면 400. Supabase REST 실패 시 502.
  - `GET /api/results` — 가게별 득표·비율(투표자 수 기준), 최근 한줄평 20개
  - `GET /api/export.csv` — UTF-8 BOM 붙은 CSV
  - `created_at`은 KST로 바꿔 `YYYY-MM-DD HH:MM:SS` 문자열로 내보낸다.
- `server.py` 구성: 설정(`load_env`) → Supabase 호출(`supabase`, `all_votes`) → 기능(`results`, `export_csv`, `parse_vote`, `save_vote`) → HTTP(`Handler.route_get`/`route_post`, `static_file`). 라우트 안에서 예외가 나면 `_respond`가 본문 없는 500을 보낸다.
- 가게 목록은 `RESTAURANTS` 하나만 고치면 투표·결과 화면이 함께 바뀐다. DB의 `picks`에 id가 저장되므로 id를 바꾸면 기존 투표가 집계에서 빠진다.

## Vercel 배포

- `vercel.json`이 `/api/*`를 `api/index.py`로 보내고, 이 파일은 `from server import Handler`로 같은 핸들러를 쓴다. 그래서 `server.py`는 import 시 서버를 띄우면 안 된다(실행은 `if __name__ == "__main__"` 안에서만).
- `.backup-clean/`은 예전 정리본 사본으로 git·배포에서 빠져 있다.
- `survey.db`는 SQLite 시절의 잔재로 지금은 쓰지 않는다.
