"""Persistência simples: reservas em memória, salvas num arquivo JSON (sem banco de dados)."""
from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.domain import Period

MEMORY = ":memory:"


@dataclass(frozen=True)
class DeskBooking:
    id: int
    desk_id: str
    day: date
    period: Period
    employee: str


def _desk_from(d: dict) -> DeskBooking:
    return DeskBooking(d["id"], d["desk_id"], date.fromisoformat(d["day"]),
                       Period(d["period"]), d["employee"])


class Repository:
    """Guarda as reservas em listas de dicionários.

    Com path=":memory:" nada é gravado em disco (usado nos testes).
    Com um caminho de arquivo, cada alteração regrava o JSON inteiro.
    """

    def __init__(self, path: str = MEMORY):
        self._path = None if path == MEMORY else Path(path)
        self._lock = threading.RLock()
        self._data = {"next_id": 1, "desks": [], "rooms": []}
        if self._path and self._path.exists():
            self._data = json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        if self._path is None:
            return
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self._path)  # troca atômica: o arquivo nunca fica pela metade

    def _new_id(self) -> int:
        new_id = self._data["next_id"]
        self._data["next_id"] += 1
        return new_id

    # ----- mesas -----
    def desk_bookings_between(self, desk_id: str, start: date, end: date) -> list[DeskBooking]:
        with self._lock:
            return [_desk_from(d) for d in self._data["desks"]
                    if d["desk_id"] == desk_id and start.isoformat() <= d["day"] <= end.isoformat()]

    def employee_desk_bookings_on(self, key: str, day: date) -> list[DeskBooking]:
        with self._lock:
            return [_desk_from(d) for d in self._data["desks"]
                    if d["employee_key"] == key and d["day"] == day.isoformat()]

    def add_desk_bookings(self, items: list[tuple[str, date, Period, str, str]]) -> list[DeskBooking]:
        """Adiciona várias reservas de uma vez e salva uma única vez."""
        with self._lock:
            created = []
            for desk_id, day, period, employee, key in items:
                record = {"id": self._new_id(), "desk_id": desk_id, "day": day.isoformat(),
                          "period": period.value, "employee": employee, "employee_key": key}
                self._data["desks"].append(record)
                created.append(_desk_from(record))
            self._save()
            return created

    def get_desk_booking(self, booking_id: int) -> tuple[DeskBooking, str] | None:
        with self._lock:
            for d in self._data["desks"]:
                if d["id"] == booking_id:
                    return _desk_from(d), d["employee_key"]
            return None

    def delete_desk_booking(self, booking_id: int) -> None:
        with self._lock:
            self._data["desks"] = [d for d in self._data["desks"] if d["id"] != booking_id]
            self._save()