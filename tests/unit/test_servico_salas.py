from datetime import date, datetime, time

import pytest

from app.domain import ConflictError, ForbiddenError, NotFoundError, Period
from app.repository import Repository
from app.services import ReservationService

AGORA = datetime(2026, 11, 25, 10, 0)  # quarta-feira
QUINTA, SEXTA = date(2026, 11, 26), date(2026, 11, 27)


@pytest.fixture
def servico():
    return ReservationService(Repository(), clock=lambda: AGORA)


def test_agenda_da_sala_vem_ordenada_pelo_inicio(servico):
    servico.book_room("S1-1", "Ana", QUINTA, time(14), time(15))
    servico.book_room("S1-1", "Bruno", QUINTA, time(9), time(10))
    assert [b.start for b in servico.room_schedule("S1-1", QUINTA)] == [time(9), time(14)]


def test_horario_sobreposto_na_mesma_sala_e_recusado(servico):
    servico.book_room("S1-1", "Ana", QUINTA, time(9), time(11))
    with pytest.raises(ConflictError, match="09:00 às 11:00"):
        servico.book_room("S1-1", "Bruno", QUINTA, time(10), time(12))


def test_reservas_encostadas_na_mesma_sala_sao_permitidas(servico):
    servico.book_room("S1-1", "Ana", QUINTA, time(9), time(10))
    servico.book_room("S1-1", "Bruno", QUINTA, time(10), time(11))
    assert len(servico.room_schedule("S1-1", QUINTA)) == 2


def test_reuniao_de_dois_dias_e_feita_com_duas_reservas(servico):
    servico.book_room("S2-1", "Ana", QUINTA, time(8), time(18))
    servico.book_room("S2-1", "Ana", SEXTA, time(8), time(18))
    assert len(servico.room_schedule("S2-1", SEXTA)) == 1


def test_mesmo_horario_em_salas_diferentes_e_permitido(servico):
    servico.book_room("S1-1", "Ana", QUINTA, time(9), time(10))
    servico.book_room("S1-2", "Bruno", QUINTA, time(9), time(10))
    assert len(servico.room_schedule("S1-2", QUINTA)) == 1


def test_sala_inexistente_e_recusada(servico):
    with pytest.raises(NotFoundError):
        servico.book_room("S7-1", "Ana", QUINTA, time(9), time(10))


def test_minhas_reservas_mostra_so_as_do_funcionario(servico):
    servico.book_desk("M1-01", "Ana Souza", [(QUINTA, Period.INTEGRAL)])
    servico.book_desk("M1-02", "Bruno", [(QUINTA, Period.INTEGRAL)])
    servico.book_room("S1-1", "Ana Souza", SEXTA, time(9), time(10))
    mesas, salas = servico.my_bookings("ana souza")
    assert [b.desk_id for b in mesas] == ["M1-01"] and [b.room_id for b in salas] == ["S1-1"]


def test_cancelar_reserva_de_mesa_libera_o_dia(servico):
    reserva = servico.book_desk("M1-01", "Ana", [(QUINTA, Period.INTEGRAL)])[0]
    servico.cancel_desk_booking(reserva.id, "Ana")
    assert QUINTA in [a.day for a in servico.desk_availability("M1-01")]


def test_nao_e_possivel_cancelar_reserva_de_outra_pessoa(servico):
    reserva = servico.book_desk("M1-01", "Ana", [(QUINTA, Period.INTEGRAL)])[0]
    with pytest.raises(ForbiddenError):
        servico.cancel_desk_booking(reserva.id, "Bruno")


def test_cancelar_reserva_inexistente_e_recusado(servico):
    with pytest.raises(NotFoundError):
        servico.cancel_room_booking(999, "Ana")


def test_cancelar_reserva_de_sala_libera_o_horario(servico):
    reserva = servico.book_room("S1-1", "Ana", QUINTA, time(9), time(10))
    servico.cancel_room_booking(reserva.id, "Ana")
    assert servico.room_schedule("S1-1", QUINTA) == []