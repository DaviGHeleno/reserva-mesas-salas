from datetime import date

import pytest

from app import domain
from app.domain import BookingError


def test_espacos_extras_no_nome_sao_removidos():
    assert domain.normalize_employee("  Ana   Souza ") == "Ana Souza"


@pytest.mark.parametrize("nome", ["", "   ", None])
def test_nome_vazio_e_recusado(nome):
    with pytest.raises(BookingError, match="nome"):
        domain.normalize_employee(nome)


def test_nome_muito_longo_e_recusado():
    with pytest.raises(BookingError, match="máximo"):
        domain.normalize_employee("a" * 81)


def test_funcionario_e_identificado_sem_diferenciar_maiusculas():
    assert domain.employee_key("ÉRICA Lima") == domain.employee_key("érica lima")


def test_assunto_muito_longo_e_cortado_em_100_caracteres():
    assert len(domain.normalize_title("x" * 300)) == 100


def test_dia_da_semana_em_portugues():
    assert domain.weekday_label(date(2026, 11, 25)) == "Quarta"


def test_data_no_formato_brasileiro():
    assert domain.format_day(date(2026, 11, 25)) == "25/11/2026"