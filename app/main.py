"""API HTTP (FastAPI)."""
from __future__ import annotations

import os
from datetime import date, datetime, time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.domain import (
    PERIOD_LABELS, BookingError, ConflictError, ForbiddenError, NotFoundError,
    Period, format_day, weekday_label,
)
from app.repository import DeskBooking, Repository, RoomBooking
from app.services import ReservationService


class Selection(BaseModel):
    day: date
    period: Period


class DeskBookingIn(BaseModel):
    employee: str
    selections: list[Selection]


class RoomBookingIn(BaseModel):
    employee: str
    day: date
    start: time
    end: time
    title: str = ""


def _day_label(day: date) -> str:
    return f"{weekday_label(day)}, {format_day(day)}"


def _desk_booking_out(b: DeskBooking) -> dict:
    return {"id": b.id, "desk_id": b.desk_id, "day": b.day.isoformat(),
            "day_label": _day_label(b.day), "period": b.period.value,
            "period_label": PERIOD_LABELS[b.period], "employee": b.employee}


def _room_booking_out(b: RoomBooking) -> dict:
    return {"id": b.id, "room_id": b.room_id, "day": b.day.isoformat(),
            "day_label": _day_label(b.day), "start": b.start.strftime("%H:%M"),
            "end": b.end.strftime("%H:%M"), "employee": b.employee, "title": b.title}


def _status_for(exc: BookingError) -> int:
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, ForbiddenError):
        return 403
    return 400


def create_app(data_file: str | None = None,
               clock: Callable[[], datetime] | None = None) -> FastAPI:
    data_file = data_file or os.environ.get("DATA_FILE", "reservas.json")
    service = ReservationService(Repository(data_file), clock)
    app = FastAPI(title="Reserva de Mesas e Salas")

    @app.exception_handler(BookingError)
    async def booking_error_handler(_: Request, exc: BookingError) -> JSONResponse:
        return JSONResponse(status_code=_status_for(exc), content={"detail": str(exc)})

    # ---------- mesas ----------
    @app.get("/api/desks")
    def list_desks(floor: int | None = None):
        return [{"id": d.id, "floor": d.floor, "number": d.number}
                for d in service.list_desks(floor)]

    @app.get("/api/desks/{desk_id}/availability")
    def desk_availability(desk_id: str):
        return [{"day": a.day.isoformat(), "label": _day_label(a.day),
                 "free": [{"value": p.value, "label": PERIOD_LABELS[p]} for p in a.free]}
                for a in service.desk_availability(desk_id)]

    @app.post("/api/desks/{desk_id}/bookings", status_code=201)
    def book_desk(desk_id: str, body: DeskBookingIn):
        created = service.book_desk(desk_id, body.employee,
                                    [(s.day, s.period) for s in body.selections])
        return [_desk_booking_out(b) for b in created]

    # ---------- salas ----------
    @app.get("/api/rooms")
    def list_rooms(floor: int | None = None):
        return [{"id": r.id, "floor": r.floor, "number": r.number}
                for r in service.list_rooms(floor)]

    @app.get("/api/rooms/{room_id}/bookings")
    def room_schedule(room_id: str, day: date):
        return [_room_booking_out(b) for b in service.room_schedule(room_id, day)]

    @app.post("/api/rooms/{room_id}/bookings", status_code=201)
    def book_room(room_id: str, body: RoomBookingIn):
        b = service.book_room(room_id, body.employee, body.day, body.start, body.end, body.title)
        return _room_booking_out(b)

    # ---------- minhas reservas ----------
    @app.get("/api/bookings")
    def my_bookings(employee: str):
        desks, rooms = service.my_bookings(employee)
        return {"desks": [_desk_booking_out(b) for b in desks],
                "rooms": [_room_booking_out(b) for b in rooms]}

    @app.delete("/api/desk-bookings/{booking_id}", status_code=204)
    def cancel_desk(booking_id: int, employee: str):
        service.cancel_desk_booking(booking_id, employee)
        return Response(status_code=204)

    @app.delete("/api/room-bookings/{booking_id}", status_code=204)
    def cancel_room(booking_id: int, employee: str):
        service.cancel_room_booking(booking_id, employee)
        return Response(status_code=204)

    return app