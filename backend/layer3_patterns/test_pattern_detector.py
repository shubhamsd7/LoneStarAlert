from __future__ import annotations

from datetime import date, timedelta

from backend.layer3_patterns.pattern_detector import detect_patterns


def test_detect_patterns_flags_bulk_filing_day() -> None:
    cases = [
        _case(case_number=f"case-{index}", filing_date=date(2026, 1, 5))
        for index in range(5)
    ]

    result = detect_patterns(cases)

    assert result["pattern"]["severity"] == "medium"
    assert result["pattern_description"] == "5 cases were filed on 2026-01-05."
    assert any(pattern["type"] == "bulk_filing_day" for pattern in result["patterns"])


def test_detect_patterns_flags_same_plaintiff_short_window() -> None:
    cases = [
        _case(
            case_number=f"case-{index}",
            plaintiff="LVNV Funding LLC",
            filing_date=date(2026, 1, 1) + timedelta(days=index),
        )
        for index in range(4)
    ]

    result = detect_patterns(cases)

    assert any(pattern["type"] == "repeat_plaintiff" for pattern in result["patterns"])
    assert "Lvnv Funding Llc filed 4 cases" in " ".join(
        pattern["description"] for pattern in result["patterns"]
    )


def test_detect_patterns_flags_zip_clustering_when_zip_exists() -> None:
    cases = [
        _case(
            case_number=f"case-{index}",
            filing_date=date(2026, 1, 1) + timedelta(days=index * 20),
            zip_code="78701",
        )
        for index in range(3)
    ]

    result = detect_patterns(cases)

    assert result["pattern_description"] == "3 cases cluster in ZIP 78701."
    assert result["pattern_severity"] == "low"
    assert result["anomaly_score"] == 0.3


def test_detect_patterns_returns_empty_payload_when_no_pattern() -> None:
    result = detect_patterns(
        [
            _case(case_number="case-1", filing_date=date(2026, 1, 1), zip_code="78701"),
            _case(case_number="case-2", filing_date=date(2026, 2, 1), zip_code="78702"),
        ]
    )

    assert result == {
        "patterns": [],
        "pattern": None,
        "pattern_description": None,
        "pattern_severity": None,
        "anomaly_score": None,
    }


def _case(
    *,
    case_number: str,
    filing_date: date,
    plaintiff: str = "Midland Credit Management",
    zip_code: str | None = None,
) -> dict:
    payload = {
        "case_number": case_number,
        "plaintiff": plaintiff,
        "filing_date": filing_date.isoformat(),
    }
    if zip_code:
        payload["zip_code"] = zip_code
    return payload
