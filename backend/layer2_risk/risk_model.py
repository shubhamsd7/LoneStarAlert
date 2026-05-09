"""Deterministic default-risk model for demo-safe TxAlert scoring."""

from __future__ import annotations

from typing import Any

from backend.layer2_risk.feature_engineer import build_case_features


def score_risk(case: Any) -> dict[str, Any]:
    """Return frontend-compatible risk scores for a case-like object or dict."""
    features = build_case_features(case)

    base_score = 0.18
    if features["is_justice_court"]:
        base_score += 0.18

    base_score += features["collector_win_rate"] * 0.30
    base_score += features["deadline_pressure"] * 0.25

    plaintiff_strength = _clamp(
        0.45
        + (features["collector_win_rate"] * 0.35)
        + (0.10 if features["is_justice_court"] else 0.0)
        + features["plaintiff_strength_adjustment"]
    )
    alert_importance = _clamp(
        0.35
        + (features["deadline_pressure"] * 0.45)
        + features["alert_importance_boost"]
    )
    default_risk_score = _clamp(base_score + (features["alert_importance_boost"] * 0.35))
    confidence = _confidence(features)

    return {
        "default_risk_score": round(default_risk_score, 2),
        "risk_confidence": confidence,
        "plaintiff_strength": round(plaintiff_strength, 2),
        "alert_importance": round(alert_importance, 2),
        "risk_level": _risk_level(default_risk_score),
        "features": features,
        "explanation": _explanation(features, default_risk_score),
    }


def _confidence(features: dict[str, Any]) -> float:
    confidence = 0.45
    if features["days_remaining"] is not None:
        confidence += 0.20
    if features["collector_win_rate"] > 0:
        confidence += 0.20
    if features["is_time_barred"] is not None:
        confidence += 0.15
    return round(_clamp(confidence), 2)


def _risk_level(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.50:
        return "medium"
    return "low"


def _explanation(features: dict[str, Any], score: float) -> str:
    reasons: list[str] = []
    if features["is_justice_court"]:
        reasons.append("justice court")
    if features["collector_win_rate"] >= 0.70:
        reasons.append("high collector default win rate")
    if features["deadline_pressure"] >= 0.75:
        reasons.append("short response deadline")
    if features["is_time_barred"] is True:
        reasons.append("possible limitations defense raises alert importance")

    if not reasons:
        reasons.append("limited deterministic risk signals")

    return f"{_risk_level(score).title()} risk based on " + ", ".join(reasons) + "."


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
