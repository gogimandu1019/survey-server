"""Vercel 서버리스 진입점: /api/* 요청을 server.py의 Handler로 처리"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import Handler  # noqa: E402


class handler(Handler):
    pass
