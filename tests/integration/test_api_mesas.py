from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

AGORA = datetime(2026, 11, 25, 10, 0)  # quarta-feira


@pytest.fixture
def cliente():
    return TestClient(create_app(":memory:", clock=lambda: AGORA))


def reservar(cliente, mesa="M1-01", funcionario="Ana", dia="2026-11-26", periodo="integral"):
    return cliente.post(f"/api/desks/{mesa}/bookings", json={
        "employee": funcionario, "selections": [{"day": dia, "period": periodo}]})


def test_lista_mesas_do_andar(cliente):
    mesas = cliente.get("/api/desks?floor=3").json()
    assert len(mesas) == 10
    assert mesas[0] == {"id": "M3-01", "floor": 3, "number": 1}


def test_disponibilidade_traz_dias_e_periodos_em_portugues(cliente):
    primeiro_dia = cliente.get("/api/desks/M1-01/availability").json()[0]
    assert primeiro_dia["label"] == "Quarta, 25/11/2026"
    assert [p["label"] for p in primeiro_dia["free"]] == ["Manhã", "Tarde", "Dia inteiro"]


def test_reserva_de_mesa_retorna_201(cliente):
    resposta = reservar(cliente)
    assert resposta.status_code == 201
    assert resposta.json()[0]["period_label"] == "Dia inteiro"


def test_mesa_ocupada_retorna_409(cliente):
    reservar(cliente)
    assert reservar(cliente, funcionario="Bruno", periodo="manha").status_code == 409


def test_dia_fora_da_janela_retorna_400_com_mensagem(cliente):
    resposta = reservar(cliente, dia="2026-12-10")
    assert resposta.status_code == 400
    assert "próxima" in resposta.json()["detail"]


def test_mesa_inexistente_retorna_404(cliente):
    assert cliente.get("/api/desks/X/availability").status_code == 404


def test_requisicao_incompleta_retorna_422(cliente):
    assert cliente.post("/api/desks/M1-01/bookings", json={"employee": "Ana"}).status_code == 422