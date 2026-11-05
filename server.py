"""삼성역 맛집 투표 서버 (Python 표준 라이브러리만 사용: http.server + sqlite3)

실행:  python server.py
투표:  http://localhost:8000/
결과:  http://localhost:8000/result
"""
import csv
import io
import json
import sqlite3
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = BASE / "survey.db"
PUBLIC = BASE / "public"
HOST, PORT = "127.0.0.1", 8000  # 이 노트북에서만 접속

# 투표 후보: 여기만 고치면 투표·결과 화면이 함께 바뀜
RESTAURANTS = [
    {"id": "hummus",  "name": "허머스키친",         "category": "중동 요리"},
    {"id": "chogye",  "name": "미사리밀빛초계국수", "category": "냉면·초계국수"},
    {"id": "haejang", "name": "중앙해장",           "category": "해장국"},
    {"id": "song",    "name": "송",                 "category": "칼국수·수제비"},
    {"id": "steak",   "name": "공대아르미",         "category": "스테이크"},
    {"id": "baekse",  "name": "백세주마을",         "category": "한식 주점"},
    {"id": "kervan",  "name": "케르반",             "category": "터키 요리"},
]
NAMES = {r["id"]: r["name"] for r in RESTAURANTS}


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                picks      TEXT NOT NULL,   -- JSON 배열 예: ["hummus","song"]
                nickname   TEXT,
                comment    TEXT,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )""")


def all_votes():
    with db() as conn:
        return conn.execute("SELECT * FROM votes ORDER BY id DESC").fetchall()


def results():
    rows = all_votes()
    counts = {r["id"]: 0 for r in RESTAURANTS}
    comments = []
    for row in rows:
        picks = json.loads(row["picks"])
        for p in picks:
            if p in counts:
                counts[p] += 1
        if row["comment"]:
            comments.append({
                "nickname": row["nickname"] or "익명",
                "text": row["comment"],
                "picks": [NAMES.get(p, p) for p in picks],
                "at": row["created_at"],
            })

    voters = len(rows)
    ranking = sorted(
        ({**r, "votes": counts[r["id"]],
          "pct": round(counts[r["id"]] / voters * 100) if voters else 0}
         for r in RESTAURANTS),
        key=lambda x: -x["votes"],
    )
    return {
        "voters": voters,
        "totalVotes": sum(counts.values()),
        "ranking": ranking,
        "comments": comments[:20],
    }


def export_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["번호", "시각", "닉네임", "선택한 가게", "한줄평"])
    for row in reversed(all_votes()):
        picks = ", ".join(NAMES.get(p, p) for p in json.loads(row["picks"]))
        w.writerow([row["id"], row["created_at"], row["nickname"] or "익명", picks, row["comment"] or ""])
    return "﻿" + buf.getvalue()  # BOM: 엑셀에서 한글 안 깨지게


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def send_body(self, status, body: bytes, content_type, extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_body(status, body, "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/restaurants":
            return self.send_json(200, RESTAURANTS)
        if path == "/api/results":
            return self.send_json(200, results())
        if path == "/api/export.csv":
            return self.send_body(200, export_csv().encode("utf-8"), "text/csv; charset=utf-8",
                                  {"Content-Disposition": 'attachment; filename="samsung-votes.csv"'})
        if path in ("/result", "/result/"):
            self.path = "/result.html"
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/votes":
            return self.send_json(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            picks = list(dict.fromkeys(p for p in data.get("picks", []) if p in NAMES))
            nickname = (data.get("nickname") or "").strip()[:20]
            comment = (data.get("comment") or "").strip()[:200]
        except (ValueError, TypeError, AttributeError):
            return self.send_json(400, {"error": "잘못된 요청이에요"})
        if not picks:
            return self.send_json(400, {"error": "가게를 한 곳 이상 골라 주세요"})

        with db() as conn:
            cur = conn.execute(
                "INSERT INTO votes (picks, nickname, comment) VALUES (?,?,?)",
                (json.dumps(picks), nickname, comment),
            )
        self.send_json(201, {"id": cur.lastrowid})


if __name__ == "__main__":
    init_db()
    print(f"투표:  http://localhost:{PORT}/")
    print(f"결과:  http://localhost:{PORT}/result")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
