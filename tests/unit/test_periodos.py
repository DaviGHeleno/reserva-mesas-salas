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