---
name: add-question
description: 맛집 투표 설문에 질문(입력 항목)을 하나 더할 때 응답 화면 → 서버 → DB → 결과 화면 → 테스트 순서로 고친다. "질문 추가", "설문 항목 추가", "새 입력칸" 요청에 사용.
---

# 설문 질문 추가

시작 전에 사용자에게 정해 둔다: 필드 이름(영문 snake_case, 예 `visit_time`), 화면 문구, 형식(짧은 글/긴 글/선택지), 필수 여부, 최대 길이, 결과 화면에 어떻게 보일지(목록·집계·CSV 열).

## 1. 응답 화면 — `public/index.html`

- 닉네임·한줄평 칸 옆에 `<label for>` + 입력 요소를 같은 클래스로 추가한다. `maxlength`는 서버 제한과 같게.
- 전송부(`x2.send(JSON.stringify({ picks, nickname, comment }))`)에 새 필드를 넣는다.
- 필수면 보내기 전에 검사하고 기존 오류 표시 방식을 그대로 쓴다.

## 2. 서버 — `server.py`

- `parse_vote`에 `_text(data, "<필드>", <한도>)`를 추가하고 반환값·`save_vote` 인자·Supabase payload에 넣는다. 선택지라면 `RESTAURANTS`처럼 상수 목록을 두고 목록 밖 값은 버린다.
- 형식이 틀리면 `BadRequest`(400 "잘못된 요청이에요"), 필수인데 비었으면 별도 400 문구.
- `results()`·`export_csv()`에서 새 필드를 읽는다. 예전 행에는 값이 없으니 `row.get("<필드>")`로 읽는다.
- `api/index.py`는 `Handler`를 그대로 쓰므로 고칠 필요 없다.

## 3. DB — `supabase/migrations/`

- 새 파일 `YYYYMMDDHHMMSS_add_<필드>.sql`: `alter table public.votes add column if not exists <필드> text;` 기존 행 때문에 `not null`은 걸지 않는다(필수 검사는 서버에서).
- RLS 정책은 추가하지 않는다. 기존 마이그레이션 파일은 고치지 않는다.
- 실제 Supabase 적용은 사용자 확인 후 진행한다. **배포는 반드시 마이그레이션 적용 후 서버 순서로** 한다(컬럼이 없으면 저장이 502).

## 4. 결과 화면 — `public/result.html`

- `/api/results` 응답의 새 값을 기존 한줄평·순위 카드 스타일로 보여 준다. 빈 값은 표시하지 않거나 "—".
- CSV에 열을 추가했다면 다운로드 버튼은 그대로 둔다.

## 5. 테스트 — `tests/`

- `tests/fake_supabase.py`는 받은 행을 그대로 저장하니 대개 수정이 필요 없다.
- `tests/test_server.py`에 추가: 저장 payload에 새 필드가 담기는지, 길이 자르기·앞뒤 공백 제거, 잘못된 타입이면 400, 필수라면 비었을 때 400, 새 필드가 없는 예전 행으로도 결과·CSV가 깨지지 않는지.
- 정확한 CSV·결과를 고정한 기존 테스트는 의도한 변화만큼만 고친다.
- 실행: `python -X utf8 -m unittest discover -s tests -v` 전체 통과 확인.
- 마지막으로 `python -X utf8 server.py`로 띄워 투표 → 결과 화면에서 새 항목이 보이는지 확인한다.
