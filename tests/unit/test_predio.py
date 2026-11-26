from app import domain


def test_predio_tem_30_mesas():
    assert len(domain.build_desks()) == 30


def test_cada_andar_tem_10_mesas():
    mesas = domain.build_desks()
    for andar in (1, 2, 3):
        assert sum(m.floor == andar for m in mesas) == 10


def test_codigos_das_mesas_sao_unicos():
    codigos = [m.id for m in domain.build_desks()]
    assert len(codigos) == len(set(codigos))


def test_predio_tem_duas_salas_por_andar():
    salas_do_segundo_andar = {s.id for s in domain.build_rooms() if s.floor == 2}
    assert salas_do_segundo_andar == {"S2-1", "S2-2"}