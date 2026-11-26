from datetime import date, datetime, time

import pytest

from app import domain
from app.domain import BookingError

AGORA = datetime(2026, 11, 25, 10, 0)  # quarta-feira, 10h
HOJE = AGORA.date()
AMANHA = date(2026, 11, 26)


def test_horarios_que_se_cruzam_se_sobrepoem():
    assert domain.intervals_overlap(time(9), time(10), time(9, 30), time(11))


def test_horario_contido_em_outro_se_sobrepoe():
    assert domain.intervals_overlap(time(9), time(12), time(10), time(11))


def test_reservas_encostadas_nao_se_sobrepoem():
    assert not domain.intervals_overlap(time(9), time(10), time(10), time(11))


def test_horarios_separados_nao_se_sobrepoem():
    assert not domain.intervals_overlap(time(13), time(14), time(9), time(10))


def test_fim_antes_do_inicio_e_proibido():
    with pytest.raises(BookingError, match="fim deve ser depois"):
        domain.validate_room_slot(AMANHA, time(11), time(10), AGORA)


def test_reserva_com_duracao_zero_e_proibida():
    with pytest.raises(BookingError, match="fim deve ser depois"):
        domain.validate_room_slot(AMANHA, time(10), time(10), AGORA)


def test_reservar_sala_em_data_passada_e_proibido():
    with pytest.raises(BookingError, match="passadas"):
        domain.validate_room_slot(date(2026, 11, 24), time(9), time(10), AGORA)


def test_reservar_sala_hoje_em_horario_que_ja_passou_e_proibido():
    with pytest.raises(BookingError, match="já passou"):
        domain.validate_room_slot(HOJE, time(9), time(11), AGORA)


def test_reservar_sala_hoje_mais_tarde_e_permitido():
    domain.validate_room_slot(HOJE, time(10), time(11), AGORA)


def test_sala_nao_tem_limite_de_data_futura():
    domain.validate_room_slot(date(2027, 6, 1), time(9), time(18), AGORA)


def test_sala_pode_ser_reservada_no_fim_de_semana():
    domain.validate_room_slot(date(2026, 11, 28), time(9), time(10), AGORA)