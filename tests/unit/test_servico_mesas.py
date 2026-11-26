from datetime import date, datetime

import pytest

from app.domain import BookingError, ConflictError, NotFoundError, Period
from app.repository import Repository
from app.services import ReservationService

AGORA = datetime(2026, 11, 25, 10, 0)  # quarta-feira
QUINTA, SEGUNDA, TERCA = date(2026, 11, 26), date(2026, 11, 30), date(2026, 12, 1)


@pytest.fixture
def servico():
    return ReservationService(Repository(), clock=lambda: AGORA)


def dias_disponiveis(servico, mesa):
    return {a.day: a.free for a in servico.desk_availability(mesa)}


def test_lista_apenas_as_mesas_do_andar_pedido(servico):
    mesas = servico.list_desks(2)
    assert len(mesas) == 10 and {m.floor for m in mesas} == {2}


def test_andar_inexistente_e_recusado(servico):
    with pytest.raises(BookingError, match="Andar"):
        servico.list_desks(4)


def test_mesa_livre_mostra_os_oito_dias_da_janela(servico):
    assert len(servico.desk_availability("M1-01")) == 8


def test_dia_reservado_inteiro_some_da_disponibilidade(servico):
    servico.book_desk("M1-01", "Ana", [(QUINTA, Period.INTEGRAL)])
    assert QUINTA not in dias_disponiveis(servico, "M1-01")


def test_mesa_reservada_de_manha_oferece_so_a_tarde(servico):
    servico.book_desk("M1-01", "Ana", [(QUINTA, Period.MANHA)])
    assert dias_disponiveis(servico, "M1-01")[QUINTA] == [Period.TARDE]


def test_reserva_de_varios_dias_cria_uma_reserva_por_dia(servico):
    criadas = servico.book_desk("M1-01", "Ana", [(QUINTA, Period.INTEGRAL), (SEGUNDA, Period.TARDE)])
    assert [(r.day, r.period) for r in criadas] == [(QUINTA, Period.INTEGRAL), (SEGUNDA, Period.TARDE)]


def test_mesa_ocupada_nao_pode_ser_reservada_por_outra_pessoa(servico):
    servico.book_desk("M1-01", "Ana", [(QUINTA, Period.MANHA)])
    with pytest.raises(ConflictError, match="não está livre"):
        servico.book_desk("M1-01", "Bruno", [(QUINTA, Period.INTEGRAL)])


def test_outra_pessoa_pode_pegar_a_tarde_de_mesa_reservada_de_manha(servico):
    servico.book_desk("M1-01", "Ana", [(QUINTA, Period.MANHA)])
    criada = servico.book_desk("M1-01", "Bruno", [(QUINTA, Period.TARDE)])[0]
    assert criada.employee == "Bruno"


def test_reserva_de_varios_dias_e_tudo_ou_nada(servico):
    servico.book_desk("M1-01", "Ana", [(TERCA, Period.INTEGRAL)])
    with pytest.raises(ConflictError):
        servico.book_desk("M1-01", "Bruno", [(SEGUNDA, Period.INTEGRAL), (TERCA, Period.INTEGRAL)])
    assert len(dias_disponiveis(servico, "M1-01")[SEGUNDA]) == 3


def test_funcionario_nao_pode_ter_duas_mesas_no_mesmo_periodo(servico):
    servico.book_desk("M1-01", "Ana", [(QUINTA, Period.INTEGRAL)])
    with pytest.raises(ConflictError, match="Você já tem"):
        servico.book_desk("M2-05", "ana", [(QUINTA, Period.MANHA)])


def test_funcionario_pode_usar_uma_mesa_de_manha_e_outra_a_tarde(servico):
    servico.book_desk("M1-01", "Ana", [(QUINTA, Period.MANHA)])
    criada = servico.book_desk("M3-10", "Ana", [(QUINTA, Period.TARDE)])[0]
    assert criada.desk_id == "M3-10"


def test_reserva_sem_nenhum_dia_e_recusada(servico):
    with pytest.raises(BookingError, match="ao menos um dia"):
        servico.book_desk("M1-01", "Ana", [])


def test_mesmo_dia_repetido_na_reserva_e_recusado(servico):
    with pytest.raises(BookingError, match="uma vez"):
        servico.book_desk("M1-01", "Ana", [(QUINTA, Period.MANHA), (QUINTA, Period.TARDE)])


def test_reserva_de_mesa_fora_da_janela_e_recusada(servico):
    with pytest.raises(BookingError, match="próxima"):
        servico.book_desk("M1-01", "Ana", [(date(2026, 12, 8), Period.INTEGRAL)])


def test_mesa_inexistente_e_recusada(servico):
    with pytest.raises(NotFoundError):
        servico.desk_availability("M9-99")