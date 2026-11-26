from datetime import date

from app import domain

QUARTA = date(2026, 11, 25)
DOMINGO = date(2026, 11, 29)


def test_janela_termina_na_sexta_da_semana_seguinte():
    assert domain.booking_window_end(QUARTA) == date(2026, 12, 4)


def test_no_domingo_a_janela_ainda_vai_ate_a_sexta_seguinte():
    assert domain.booking_window_end(DOMINGO) == date(2026, 12, 4)


def test_dias_reservaveis_comecam_hoje():
    assert domain.bookable_desk_days(QUARTA)[0] == QUARTA


def test_dias_reservaveis_nao_incluem_fim_de_semana():
    dias = domain.bookable_desk_days(QUARTA)
    assert all(d.weekday() < 5 for d in dias)


def test_de_quarta_ha_oito_dias_reservaveis():
    assert len(domain.bookable_desk_days(QUARTA)) == 8