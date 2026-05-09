from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, timedelta

import pytest

from backend.services.collector_scorer import (
    CLUSTERED_FILING_ERROR,
    IMPROPER_SERVICE_ERROR,
    ROUND_AMOUNT_ERROR,
    CollectorProfile,
    score_collector,
)


def test_high_threat_collector_detects_patterns() -> None:
    cases = _cases(
        count=30,
        default_wins=24,
        amount=5000,
        improper_service_count=5,
        clustered=True,
    )

    profile = score_collector("Midland Credit Management", cases)

    assert profile.threat_level == "HIGH"
    assert profile.total_cases == 30
    assert profile.default_win_rate == 0.8
    assert profile.avg_claim_amount == 5000.0
    assert IMPROPER_SERVICE_ERROR in profile.common_errors
    assert ROUND_AMOUNT_ERROR in profile.common_errors
    assert CLUSTERED_FILING_ERROR in profile.common_errors


def test_medium_threat_collector_from_moderate_volume_and_default_rate() -> None:
    cases = _cases(count=12, default_wins=5, amount=1234.56)

    profile = score_collector("LVNV Funding", cases)

    assert profile.threat_level == "MEDIUM"
    assert profile.total_cases == 12
    assert round(profile.default_win_rate, 2) == 0.42
    assert profile.common_errors == []


def test_low_threat_collector_with_small_history_and_no_patterns() -> None:
    cases = _cases(count=3, default_wins=0, amount=875.25)

    profile = score_collector("Local Finance", cases)

    assert profile.threat_level == "LOW"
    assert profile.total_cases == 3
    assert profile.default_win_rate == 0.0
    assert profile.avg_claim_amount == 875.25
    assert profile.common_errors == []


def test_matching_plaintiff_filter_uses_relevant_history() -> None:
    cases = _cases(
        count=4,
        default_wins=4,
        amount=5000,
        plaintiff="Other Collector",
    ) + _cases(
        count=2,
        default_wins=0,
        amount=900,
        plaintiff="Target Collector",
    )

    profile = score_collector("Target Collector", cases)

    assert profile.total_cases == 2
    assert profile.default_win_rate == 0.0
    assert profile.avg_claim_amount == 900.0
    assert profile.threat_level == "LOW"


def test_empty_history_returns_low_threat_profile() -> None:
    profile = score_collector("Unknown Collector", [])

    assert profile == CollectorProfile(
        plaintiff_name="Unknown Collector",
        total_cases=0,
        default_win_rate=0.0,
        avg_claim_amount=0.0,
        common_errors=[],
        threat_level="LOW",
    )


def test_result_contract_is_frozen_dataclass() -> None:
    profile = score_collector("LVNV Funding", _cases(count=1, default_wins=0))

    assert isinstance(profile, CollectorProfile)
    with pytest.raises(FrozenInstanceError):
        profile.threat_level = "HIGH"


def _cases(
    *,
    count: int,
    default_wins: int,
    amount: float = 1000,
    plaintiff: str = "Midland Credit Management",
    improper_service_count: int = 0,
    clustered: bool = False,
) -> list[dict]:
    base_date = date(2026, 1, 1)
    cases = []

    for index in range(count):
        filing_date = (
            base_date + timedelta(days=index % 3)
            if clustered and index < 3
            else base_date + timedelta(days=index * 14)
        )
        cases.append(
            {
                "plaintiff": plaintiff,
                "filing_date": filing_date.isoformat(),
                "amount_claimed": amount,
                "outcome": (
                    "Default judgment granted"
                    if index < default_wins
                    else "Dismissed"
                ),
                "notes": (
                    "Possible improper service"
                    if index < improper_service_count
                    else "No noted service issue"
                ),
            }
        )

    return cases
