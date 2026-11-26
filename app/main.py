"""API HTTP (FastAPI)."""
from __future__ import annotations

import os
from datetime import date, datetime
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.domain import (
    PERIOD_LABELS, BookingError, ConflictError, ForbiddenError, NotFoundError,
    Period, format_day, weekday_label,
)
from app.repository import DeskBooking, Repository
from app.services import ReservationService


class Selection(BaseModel):
    day: date
    period: Period


class DeskBookingIn(BaseModel):
    employee: str
    selections: list[Selection]


def _day_label(day: date) -> str:
    return f"{weekday_label(day)}, {format_day(day)}"


def _desk_booking_out(b: DeskBooking) -> dict:
    return {"id": b.id, "desk_id": b.desk_id, "day": b.day.isoformat(),
            "day_label": _day_label(b.day), "period": b.period.value,
            "period_label": PERIOD_LABELS[b.period], "employee": b.employee}


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

    return app