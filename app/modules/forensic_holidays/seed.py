"""Idempotent seed for forensic_holidays.

Usage:
    python -m app.modules.forensic_holidays.seed [year ...]

Default: seeds current year and next year (so prazos straddling year-end work).
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

from app.db.database import SessionLocal
from app.modules.forensic_holidays.model import ForensicHoliday, HolidayScope
from app.modules.forensic_holidays.repository import ForensicHolidayRepository

DATA_FILE = Path(__file__).parent / "data" / "holidays.json"


def _load_data() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _recess_dates(start_year: int, data: dict) -> list[tuple[date, str]]:
    recess = data["recess"]
    start = date(start_year, recess["start_month"], recess["start_day"])
    end = date(start_year + 1, recess["end_month"], recess["end_day"])
    out: list[tuple[date, str]] = []
    d = start
    while d <= end:
        out.append((d, recess["description"]))
        d += timedelta(days=1)
    return out


def _entries_for_year(
    year: int, data: dict
) -> list[tuple[date, str, HolidayScope, str | None, str | None]]:
    entries: list[tuple[date, str, HolidayScope, str | None, str | None]] = []

    for item in data["national_fixed"]:
        entries.append(
            (
                date(year, item["month"], item["day"]),
                item["description"],
                HolidayScope.NATIONAL,
                None,
                None,
            )
        )

    for item in data["court_TJDFT"]:
        entries.append(
            (
                date(year, item["month"], item["day"]),
                item["description"],
                HolidayScope.COURT,
                "TJDFT",
                None,
            )
        )

    for d, desc in _recess_dates(year, data):
        entries.append((d, desc, HolidayScope.NATIONAL, None, None))

    return entries


def seed_years(years: list[int]) -> dict[str, int]:
    data = _load_data()
    created = 0
    skipped = 0

    with SessionLocal() as db:
        repo = ForensicHolidayRepository(db)
        for year in years:
            for d, desc, scope, court, comarca in _entries_for_year(year, data):
                existing = repo.get_by_natural_key(d, scope, court, comarca)
                if existing is not None:
                    skipped += 1
                    continue
                holiday = ForensicHoliday(
                    date=d,
                    description=desc,
                    scope=scope,
                    court=court,
                    comarca=comarca,
                )
                db.add(holiday)
                created += 1
            db.commit()

    return {"created": created, "skipped": skipped}


def main() -> None:
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]
    else:
        current = date.today().year
        years = [current, current + 1]

    result = seed_years(years)
    print(f"Seed forensic_holidays years={years}: {result}")


if __name__ == "__main__":
    main()
