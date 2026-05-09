from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, datetime

import pytest

from backend.services.limitations_checker import (
    LimitationsResult,
    _classify_defense_strength,
    _parse_optional_date,
    check_statute_of_limitations,
)


@pytest.mark.parametrize(
    ("elapsed_years", "defense_strength"),
    [
        (4.01, "STRONG"),
        (4.0, "BORDERLINE"),
        (3.51, "BORDERLINE"),
        (3.5, "UNLIKELY"),
        (3.01, "UNLIKELY"),
        (3.0, "NONE"),
        (1.0, "NONE"),
    ],
)
def test_defense_strength_thresholds(
    elapsed_years: float, defense_strength: str
) -> None:
    assert _classify_defense_strength(elapsed_years) == defense_strength


def test_strong_defense_when_elapsed_more_than_four_years() -> None:
    result = check_statute_of_limitations(
        debt_origin_date=date(2020, 1, 1),
        as_of_date=date(2024, 1, 2),
    )

    assert result.defense_strength == "STRONG"
    assert result.is_time_barred is True
    assert result.elapsed_years > 4.0
    assert result.limitations_years == 4.0


def test_borderline_defense_when_elapsed_between_three_and_half_and_four_years() -> None:
    result = check_statute_of_limitations(
        debt_origin_date=date(2020, 1, 1),
        as_of_date=date(2023, 10, 1),
    )

    assert result.defense_strength == "BORDERLINE"
    assert result.is_time_barred is False


def test_unlikely_defense_when_elapsed_between_three_and_three_and_half_years() -> None:
    result = check_statute_of_limitations(
        debt_origin_date=date(2020, 1, 1),
        as_of_date=date(2023, 4, 1),
    )

    assert result.defense_strength == "UNLIKELY"
    assert result.is_time_barred is False


def test_no_defense_when_elapsed_three_years_or_less() -> None:
    result = check_statute_of_limitations(
        debt_origin_date=date(2020, 1, 1),
        as_of_date=date(2022, 12, 31),
    )

    assert result.defense_strength == "NONE"
    assert result.is_time_barred is False


def test_last_payment_date_restarts_limitations_clock() -> None:
    result = check_statute_of_limitations(
        debt_origin_date=date(2019, 1, 1),
        last_payment_date=date(2022, 1, 1),
        as_of_date=date(2024, 1, 1),
    )

    assert result.clock_start_date == date(2022, 1, 1)
    assert result.defense_strength == "NONE"
    assert result.is_time_barred is False


def test_result_contract_is_frozen_dataclass() -> None:
    result = check_statute_of_limitations(
        debt_origin_date=date(2020, 1, 1),
        as_of_date=date(2024, 1, 2),
    )

    assert isinstance(result, LimitationsResult)
    with pytest.raises(FrozenInstanceError):
        result.defense_strength = "NONE"


def test_accepts_date_datetimes_and_iso_strings() -> None:
    result = check_statute_of_limitations(
        debt_origin_date="2020-01-01T09:30:00Z",
        debt_type="Consumer Debt",
        last_payment_date=datetime(2020, 6, 1, 12, 0),
        as_of_date=date(2024, 1, 1),
    )

    assert result.clock_start_date == date(2020, 6, 1)
    assert result.debt_type == "consumer_debt"
    assert _parse_optional_date("2024-01-01") == date(2024, 1, 1)


def test_invalid_inputs_raise_value_error() -> None:
    with pytest.raises(ValueError, match="debt_origin_date is required"):
        check_statute_of_limitations("")

    with pytest.raises(ValueError, match="Cannot parse date"):
        check_statute_of_limitations("not-a-date")

    with pytest.raises(ValueError, match="Cannot parse date"):
        check_statute_of_limitations(date(2020, 1, 1), as_of_date="not-a-date")
