"""Regras de negócio puras do sistema de reservas (sem banco, sem HTTP)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

FLOORS = 3
DESKS_PER_FLOOR = 10
ROOMS_PER_FLOOR = 2


class BookingError(Exception):
    """Requisição que viola uma regra de negócio."""


class ConflictError(BookingError):
    """O recurso já está ocupado."""


class NotFoundError(BookingError):
    """Mesa, sala ou reserva inexistente."""


class ForbiddenError(BookingError):
    """O funcionário tentou alterar a reserva de outra pessoa."""


@dataclass(frozen=True)
class Desk:
    id: str
    floor: int
    number: int


@dataclass(frozen=True)
class Room:
    id: str
    floor: int
    number: int


def build_desks() -> list[Desk]:
    """Mesas do prédio: M1-01 até M3-10."""
    return [
        Desk(f"M{floor}-{n:02d}", floor, n)
        for floor in range(1, FLOORS + 1)
        for n in range(1, DESKS_PER_FLOOR + 1)
    ]


def build_rooms() -> list[Room]:
    """Salas de reunião do prédio: S1-1 até S3-2."""
    return [
        Room(f"S{floor}-{n}", floor, n)
        for floor in range(1, FLOORS + 1)
        for n in range(1, ROOMS_PER_FLOOR + 1)
    ]


class Period(str, Enum):
    MANHA = "manha"
    TARDE = "tarde"
    INTEGRAL = "integral"


PERIOD_LABELS = {
    Period.MANHA: "Manhã",
    Period.TARDE: "Tarde",
    Period.INTEGRAL: "Dia inteiro",
}


def periods_conflict(a: Period, b: Period) -> bool:
    """Dia inteiro conflita com tudo; manhã e tarde só conflitam consigo mesmas."""
    return a is Period.INTEGRAL or b is Period.INTEGRAL or a is b


def free_periods(taken: set[Period]) -> list[Period]:
    """Períodos que ainda podem ser reservados, dado o que já está ocupado."""
    return [p for p in Period if all(not periods_conflict(p, t) for t in taken)]