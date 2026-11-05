"""server.py를 고치지 않고 다른 포트로 띄우는 실행기.

사용: python -X utf8 tests/run_server.py <server.py 경로> <포트>

server.py는 포트 8000을 코드에 박아 두었으므로, socket.bind를 가로채
8000 대신 지정한 포트로 바꾼다. raw socket 구현이든 http.server 구현이든
결국 socket.bind를 부르므로 리팩터링 전후 모두 같은 방식으로 띄울 수 있다.
"""
import os
import runpy
import socket
import sys

server_path = os.path.abspath(sys.argv[1])
port = int(sys.argv[2])

_orig_bind = socket.socket.bind


def _bind(self, address):
    if isinstance(address, tuple) and len(address) >= 2 and address[1] == 8000:
        address = (address[0], port) + tuple(address[2:])
    return _orig_bind(self, address)


socket.socket.bind = _bind
sys.argv = [server_path]
sys.path.insert(0, os.path.dirname(server_path))
runpy.run_path(server_path, run_name="__main__")
