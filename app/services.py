"""Casos de uso: combinam as regras do domínio com o repositório."""
from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Callable
from zoneinfo import ZoneInfo

from app.domain import (
    FLOORS, PERIOD_LABELS, BookingError, ConflictError, Desk, ForbiddenError,
    NotFoundError, Period, Room, bookable_desk_days, build_desks, build_rooms,
    employee_key, format_day, free_periods, intervals_overlap, normalize_employee,
    normalize_title, periods_conflict, validate_desk_day, validate_room_slot,
)
from app.repository import DeskBooking, Repository, RoomBooking

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
        self._rooms = {r.id: r for r in build_rooms()}

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

    # ---------- salas ----------
    def list_rooms(self, floor: int | None = None) -> list[Room]:
        _check_floor(floor)
        return [r for r in self._rooms.values() if floor is None or r.floor == floor]

    def _room(self, room_id: str) -> Room:
        if room_id not in self._rooms:
            raise NotFoundError("Sala não encontrada.")
        return self._rooms[room_id]

    def room_schedule(self, room_id: str, day: date) -> list[RoomBooking]:
        self._room(room_id)
        return self._repo.room_bookings_on(room_id, day)

    def book_room(self, room_id: str, employee: str, day: date, start: time, end: time,
                  title: str = "") -> RoomBooking:
        self._room(room_id)
        name = normalize_employee(employee)
        validate_room_slot(day, start, end, self._clock())
        with self._lock:
            for b in self._repo.room_bookings_on(room_id, day):
                if intervals_overlap(start, end, b.start, b.end):
                    raise ConflictError(
                        f"A sala já está reservada das {b.start:%H:%M} às {b.end:%H:%M}."
                    )
            return self._repo.add_room_booking(
                room_id, day, start, end, name, employee_key(name), normalize_title(title)
            )

    # ---------- reservas do funcionário ----------
    def my_bookings(self, employee: str) -> tuple[list[DeskBooking], list[RoomBooking]]:
        return self._repo.bookings_of(employee_key(employee), self.today())

    def cancel_desk_booking(self, booking_id: int, employee: str) -> None:
        found = self._repo.get_desk_booking(booking_id)
        if found is None:
            raise NotFoundError("Reserva não encontrada.")
        if found[1] != employee_key(employee):
            raise ForbiddenError("Você só pode cancelar as suas próprias reservas.")
        self._repo.delete_desk_booking(booking_id)

    def cancel_room_booking(self, booking_id: int, employee: str) -> None:
        found = self._repo.get_room_booking(booking_id)
        if found is None:
            raise NotFoundError("Reserva não encontrada.")
        if found[1] != employee_key(employee):
            raise ForbiddenError("Você só pode cancelar as suas próprias reservas.")
        self._repo.delete_room_booking(booking_id)


def _check_floor(floor: int | None) -> None:
    if floor is not None and not 1 <= floor <= FLOORS:
        raise BookingError(f"Andar inválido. Use de 1 a {FLOORS}.")