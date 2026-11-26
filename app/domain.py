"""Regras de negócio puras do sistema de reservas (sem banco, sem HTTP)."""
from __future__ import annotations

from dataclasses import dataclass

FLOORS = 3
DESKS_PER_FLOOR = 10
ROOMS_PER_FLOOR = 2


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