from fastapi.testclient import TestClient

from app.main import create_app


def test_pagina_inicial_e_servida_em_portugues():
    resposta = TestClient(create_app(":memory:")).get("/")
    assert resposta.status_code == 200
    assert "Reservas do Escritório" in resposta.text