"""Casos de uso: combinam as regras do domínio com o repositório."""
from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable
from zoneinfo import ZoneInfo

from app.domain import (
    FLOORS, PERIOD_LABELS, BookingError, ConflictError, Desk, NotFoundError, Period,
    bookable_desk_days, build_desks, employee_key, format_day, free_periods,
    normalize_employee, periods_conflict, validate_desk_day,
)
from app.repository import DeskBooking, Repository

TIMEZONE = ZoneInfo("America/Sao_Paulo")


def now_sao_paulo() -> datetime:
    """Data e hora atuais no horário de Brasília."""
    return datetime.now(TIMEZONE).replace(tzinfo=None)


@dataclass(frozen=True)
class DayAvailability:
    day: date
    free: list[Period]


class ReservationService:
    def __init__(self, repo: Repository, clock: Callable[[], datetime] | None = None):
        self._repo = repo
        self._clock = clock or now_sao_paulo
        self._lock = threading.Lock()
        self._desks = {d.id: d for d in build_desks()}

    def today(self) -> date:
        return self._clock().date()

    # ---------- mesas ----------
    def list_desks(self, floor: int | None = None) -> list[Desk]:
        _check_floor(floor)
        return [d for d in self._desks.values() if floor is None or d.floor == floor]

    def _desk(self, desk_id: str) -> Desk:
        if desk_id not in self._desks:
            raise NotFoundError("Mesa não encontrada.")
        return self._desks[desk_id]

    def desk_availability(self, desk_id: str) -> list[DayAvailability]:
        """Dias reserváveis (esta semana e a próxima) em que a mesa tem algum período livre."""
        self._desk(desk_id)
        days = bookable_desk_days(self.today())
        taken: dict[date, set[Period]] = defaultdict(set)
        for b in self._repo.desk_bookings_between(desk_id, days[0], days[-1]):
            taken[b.day].add(b.period)
        result = []
        for day in days:
            free = free_periods(taken[day])
            if free:
                result.append(DayAvailability(day, free))
        return result

    def book_desk(self, desk_id: str, employee: str,
                  selections: list[tuple[date, Period]]) -> list[DeskBooking]:
        """Reserva vários dias de uma vez; se algum dia falhar, nenhum é reservado."""
        self._desk(desk_id)
        name = normalize_employee(employee)
        key = employee_key(name)
        if not selections:
            raise BookingError("Selecione ao menos um dia.")
        days = [day for day, _ in selections]
        if len(set(days)) != len(days):
            raise BookingError("Cada dia só pode aparecer uma vez na reserva.")
        today = self.today()
        for day in days:
            validate_desk_day(day, today)

        with self._lock:
            for day, period in selections:
                taken = {b.period for b in self._repo.desk_bookings_between(desk_id, day, day)}
                if any(periods_conflict(period, t) for t in taken):
                    raise ConflictError(
                        f"A mesa {desk_id} não está livre em {format_day(day)} "
                        f"({PERIOD_LABELS[period]})."
                    )
                mine = self._repo.employee_desk_bookings_on(key, day)
                if any(periods_conflict(period, b.period) for b in mine):
                    raise ConflictError(
                        f"Você já tem uma mesa reservada em {format_day(day)} nesse período."
                    )
            return self._repo.add_desk_bookings(
                [(desk_id, day, period, name, key) for day, period in selections]
            )


def _check_floor(floor: int | None) -> None:
    if floor is not None and not 1 <= floor <= FLOORS:
        raise BookingError(f"Andar inválido. Use de 1 a {FLOORS}.")