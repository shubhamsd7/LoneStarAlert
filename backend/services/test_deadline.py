from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta

import pytest

from backend.services.deadline_calculator import (
    DeadlineResult,
    _calculate_urgency,
    _next_monday_after,
    _parse_optional_date,
    calculate_deadline,
)


def test_justice_court_deadline_is_14_days_from_service() -> None:
    result = calculate_deadline(
        filing_date=date(2026, 1, 2),
        court_type="justice",
        service_date=date(2026, 1, 5),
    )

    assert result == DeadlineResult(
        deadline_date=date(2026, 1, 19),
        days_remaining=(date(2026, 1, 19) - date.today()).days,
        urgency_level=_calculate_urgency((date(2026, 1, 19) - date.today()).days),
        court_type="justice",
        response_window_days=14,
    )


def test_district_court_deadline_is_next_monday_after_20_days() -> None:
    result = calculate_deadline(
        filing_date=date(2026, 1, 2),
        court_type="district",
        service_date=date(2026, 1, 5),
    )

    assert date(2026, 1, 25).weekday() == 6
    assert result.deadline_date == date(2026, 1, 26)
    assert result.court_type == "district"
    assert result.response_window_days == 20


def test_district_court_uses_monday_after_when_20_day_mark_is_monday() -> None:
    result = calculate_deadline(
        filing_date=date(2026, 1, 6),
        court_type="county",
        service_date=date(2026, 1, 6),
    )

    assert date(2026, 1, 26).weekday() == 0
    assert result.deadline_date == date(2026, 2, 2)
    assert result.court_type == "county"


def test_missing_service_date_uses_filing_date_plus_three_as_start_date() -> None:
    result = calculate_deadline(
        filing_date=date(2026, 2, 3),
        court_type="justice",
    )

    assert result.deadline_date == date(2026, 2, 20)


@pytest.mark.parametrize(
    ("court_type", "normalized"),
    [
        ("Justice Court Precinct 1", "justice"),
        ("JP", "justice"),
        ("District Court", "district"),
        ("County Court at Law", "county"),
    ],
)
def test_court_type_normalization(court_type: str, normalized: str) -> None:
    result = calculate_deadline(date(2026, 1, 2), court_type, date(2026, 1, 5))

    assert result.court_type == normalized


@pytest.mark.parametrize(
    ("days_remaining", "urgency"),
    [
        (-1, "CRITICAL"),
        (3, "CRITICAL"),
        (4, "URGENT"),
        (7, "URGENT"),
        (8, "WARNING"),
        (14, "WARNING"),
        (15, "MONITOR"),
    ],
)
def test_urgency_thresholds(days_remaining: int, urgency: str) -> None:
    assert _calculate_urgency(days_remaining) == urgency


def test_result_contract_is_frozen_dataclass() -> None:
    result = calculate_deadline(date(2026, 1, 2), "justice", date(2026, 1, 5))

    assert isinstance(result, DeadlineResult)
    with pytest.raises(FrozenInstanceError):
        result.days_remaining = 10


def test_date_parser_accepts_dates_datetimes_and_iso_strings() -> None:
    assert _parse_optional_date(date(2026, 1, 2)) == date(2026, 1, 2)
    assert _parse_optional_date(datetime(2026, 1, 2, 9, 30)) == date(2026, 1, 2)
    assert _parse_optional_date("2026-01-02T09:30:00Z") == date(2026, 1, 2)


def test_invalid_inputs_raise_value_error() -> None:
    with pytest.raises(ValueError, match="filing_date is required"):
        calculate_deadline("", "justice")

    with pytest.raises(ValueError, match="court_type must be"):
        calculate_deadline(date(2026, 1, 2), "probate")

    with pytest.raises(ValueError, match="Cannot parse date"):
        calculate_deadline(date(2026, 1, 2), "justice", "not-a-date")


def test_next_monday_after_is_strictly_after_input_date() -> None:
    monday = date(2026, 1, 5)

    assert _next_monday_after(monday) == monday + timedelta(days=7)
    assert _next_monday_after(date(2026, 1, 6)) == date(2026, 1, 12)
