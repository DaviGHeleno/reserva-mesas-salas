from datetime import date, time

from app.domain import Period
from app.repository import Repository

QUINTA = date(2026, 11, 26)


def reservar_mesa(repo, mesa="M1-01", dia=QUINTA, funcionario="Ana"):
    return repo.add_desk_bookings([(mesa, dia, Period.MANHA, funcionario, funcionario.lower())])[0]


def test_reservas_recebem_ids_sequenciais():
    repo = Repository()
    primeira = reservar_mesa(repo)
    segunda = reservar_mesa(repo, mesa="M1-02")
    assert segunda.id == primeira.id + 1


def test_reservas_continuam_salvas_ao_reabrir_o_arquivo(tmp_path):
    arquivo = str(tmp_path / "reservas.json")
    reservar_mesa(Repository(arquivo))
    reaberto = Repository(arquivo)
    assert len(reaberto.desk_bookings_between("M1-01", QUINTA, QUINTA)) == 1


def test_modo_em_memoria_nao_cria_arquivo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reservar_mesa(Repository())
    assert list(tmp_path.iterdir()) == []


def test_reserva_de_mesa_excluida_deixa_de_existir():
    repo = Repository()
    reserva = reservar_mesa(repo)
    repo.delete_desk_booking(reserva.id)
    assert repo.get_desk_booking(reserva.id) is None


def test_reservas_de_sala_vem_ordenadas_pelo_inicio():
    repo = Repository()
    repo.add_room_booking("S1-1", QUINTA, time(14), time(15), "Ana", "ana", "")
    repo.add_room_booking("S1-1", QUINTA, time(9), time(10), "Bruno", "bruno", "")
    inicios = [b.start for b in repo.room_bookings_on("S1-1", QUINTA)]
    assert inicios == [time(9), time(14)]


def test_reservas_do_funcionario_ignoram_datas_anteriores():
    repo = Repository()
    reservar_mesa(repo, dia=date(2026, 11, 20))
    reservar_mesa(repo, dia=QUINTA)
    mesas, _ = repo.bookings_of("ana", from_day=QUINTA)
    assert [b.day for b in mesas] == [QUINTA]