from __future__ import annotations

from backend.layer2_risk.feature_engineer import build_case_features
from backend.layer2_risk.risk_model import score_risk


def test_score_risk_raises_default_risk_for_justice_high_win_rate_and_deadline() -> None:
    result = score_risk(
        {
            "court_type": "justice",
            "collector_win_rate": 0.90,
            "days_remaining": 2,
            "is_time_barred": False,
        }
    )

    assert result["risk_level"] == "high"
    assert result["default_risk_score"] >= 0.75
    assert result["risk_confidence"] == 1.0
    assert result["plaintiff_strength"] > 0.70


def test_time_barred_debt_lowers_plaintiff_strength_but_raises_alert_importance() -> None:
    result = score_risk(
        {
            "court_type": "district",
            "collector_win_rate": 0.40,
            "days_remaining": 5,
            "is_time_barred": True,
        }
    )

    assert result["plaintiff_strength"] < 0.50
    assert result["alert_importance"] >= 0.85
    assert "limitations defense" in result["explanation"]


def test_build_case_features_handles_missing_values() -> None:
    features = build_case_features({"court_type": "district"})

    assert features["is_justice_court"] is False
    assert features["collector_win_rate"] == 0.0
    assert features["deadline_pressure"] == 0.20
    assert features["is_time_barred"] is None
