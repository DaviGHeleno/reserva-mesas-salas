from datetime import time

from app import domain


def test_horarios_que_se_cruzam_se_sobrepoem():
    assert domain.intervals_overlap(time(9), time(10), time(9, 30), time(11))


def test_horario_contido_em_outro_se_sobrepoe():
    assert domain.intervals_overlap(time(9), time(12), time(10), time(11))


def test_reservas_encostadas_nao_se_sobrepoem():
    assert not domain.intervals_overlap(time(9), time(10), time(10), time(11))


def test_horarios_separados_nao_se_sobrepoem():
    assert not domain.intervals_overlap(time(13), time(14), time(9), time(10))