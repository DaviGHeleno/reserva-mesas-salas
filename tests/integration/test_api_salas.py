from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

AGORA = datetime(2026, 11, 25, 10, 0)  # quarta-feira


@pytest.fixture
def cliente():
    return TestClient(create_app(":memory:", clock=lambda: AGORA))


def reservar_sala(cliente, funcionario="Ana", inicio="09:00", fim="10:00"):
    return cliente.post("/api/rooms/S1-1/bookings", json={
        "employee": funcionario, "day": "2026-11-26", "start": inicio, "end": fim,
        "title": "Daily"})


def test_lista_as_seis_salas_do_predio(cliente):
    assert len(cliente.get("/api/rooms").json()) == 6


def test_reserva_de_sala_aparece_na_agenda_do_dia(cliente):
    assert reservar_sala(cliente, inicio="09:00", fim="10:30").status_code == 201
    agenda = cliente.get("/api/rooms/S1-1/bookings?day=2026-11-26").json()
    assert (agenda[0]["start"], agenda[0]["end"]) == ("09:00", "10:30")


def test_sala_com_fim_antes_do_inicio_retorna_400(cliente):
    assert reservar_sala(cliente, inicio="15:00", fim="14:00").status_code == 400


def test_minhas_reservas_lista_a_reserva_feita(cliente):
    id_reserva = reservar_sala(cliente).json()["id"]
    minhas = cliente.get("/api/bookings?employee=Ana").json()
    assert [r["id"] for r in minhas["rooms"]] == [id_reserva]


def test_cancelar_a_propria_reserva_retorna_204(cliente):
    id_reserva = reservar_sala(cliente).json()["id"]
    assert cliente.delete(f"/api/room-bookings/{id_reserva}?employee=Ana").status_code == 204


def test_cancelar_reserva_de_outra_pessoa_retorna_403(cliente):
    id_reserva = reservar_sala(cliente).json()["id"]
    assert cliente.delete(f"/api/room-bookings/{id_reserva}?employee=Bruno").status_code == 403


def test_cancelar_reserva_de_mesa_inexistente_retorna_404(cliente):
    assert cliente.delete("/api/desk-bookings/999?employee=Ana").status_code == 404