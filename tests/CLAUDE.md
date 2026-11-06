# tests

- 리팩터링 안전망. 현재 동작을 그대로 기록한 것이라 동작을 일부러 바꾸려면 테스트를 먼저 고친다.
- `fake_supabase.py`가 가짜 PostgREST를 띄우고, `run_server.py`가 `socket.bind`를 가로채 포트 8000 대신 빈 포트로 `server.py`를 별도 프로세스로 실행한다.
- 실제 Supabase·`.env.local`은 쓰지 않고 내부 구현에 기대지 않아 리팩터링 뒤에도 그대로 돌린다.
- 다른 구현을 검사하려면 `SURVEY_SERVER=<server.py 경로>`.
