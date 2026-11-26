"""Sobe o site num servidor real, com dados temporários, para os testes de ponta a ponta."""
import socket
import threading
import time

import pytest
import uvicorn

from app.main import create_app


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def server_url(tmp_path_factory):
    arquivo = tmp_path_factory.mktemp("dados") / "e2e.json"
    porta = _porta_livre()
    servidor = uvicorn.Server(uvicorn.Config(create_app(str(arquivo)), host="127.0.0.1",
                                             port=porta, log_level="warning"))
    thread = threading.Thread(target=servidor.run, daemon=True)
    thread.start()
    limite = time.time() + 15
    while not servidor.started:
        if time.time() > limite:
            raise RuntimeError("O servidor de teste não iniciou")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{porta}"
    servidor.should_exit = True
    thread.join(timeout=5)