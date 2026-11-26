import pytest

from app import domain
from app.domain import Period


@pytest.mark.parametrize("outro", list(Period))
def test_dia_inteiro_conflita_com_qualquer_periodo(outro):
    assert domain.periods_conflict(Period.INTEGRAL, outro)


def test_manha_e_tarde_nao_conflitam():
    assert not domain.periods_conflict(Period.MANHA, Period.TARDE)


def test_mesmo_meio_periodo_conflita():
    assert domain.periods_conflict(Period.TARDE, Period.TARDE)


def test_sem_reservas_todos_os_periodos_estao_livres():
    assert domain.free_periods(set()) == [Period.MANHA, Period.TARDE, Period.INTEGRAL]


def test_reserva_de_manha_deixa_so_a_tarde_livre():
    assert domain.free_periods({Period.MANHA}) == [Period.TARDE]


def test_reserva_de_dia_inteiro_nao_deixa_nada_livre():
    assert domain.free_periods({Period.INTEGRAL}) == []


def test_manha_e_tarde_reservadas_nao_deixam_nada_livre():
    assert domain.free_periods({Period.MANHA, Period.TARDE}) == []