"""Case analysis agent."""

from __future__ import annotations

import json
import os
from datetime import date
from decimal import Decimal
from typing import Any

from backend.models.case import CourtCase


SYSTEM_PROMPT = (
    "You are a Texas legal aid information assistant. Analyze this public court "
    "record for practical legal information. Do not provide legal advice. Focus "
    "on statute of limitations, service issues, debt ownership proof, amount "
    "disputes, and bankruptcy discharge. Return JSON only."
)

DEFAULT_ANALYSIS = {
    "defenses": [],
    "strongest_defense": "Respond before the deadline and contact legal aid.",
    "urgency_note": "Deadline information is unavailable. Check the court record.",
    "plain_language_summary": (
        "A public court record may need review. This is legal information, not "
        "legal advice."
    ),
}


def analyze_case(case: CourtCase) -> dict[str, Any]:
    """Analyze a court case using deterministic signals first.

    OpenAI enhancement is optional. If the API key, package, or network call is
    unavailable, the deterministic analysis is returned.
    """
    deterministic = _deterministic_analysis(case)
    llm_analysis = _optional_openai_analysis(case, deterministic)
    if not llm_analysis:
        return deterministic

    return _merge_analysis(deterministic, llm_analysis)


def _deterministic_analysis(case: CourtCase) -> dict[str, Any]:
    defenses = _deterministic_defenses(case)
    strongest_defense = defenses[0] if defenses else DEFAULT_ANALYSIS["strongest_defense"]

    analysis = {
        "defenses": defenses,
        "strongest_defense": strongest_defense,
        "urgency_note": _urgency_note(case),
        "plain_language_summary": _plain_language_summary(case, strongest_defense),
        "deterministic_signals": {
            "deadline_date": _date_to_str(case.deadline_date),
            "days_remaining": case.days_remaining,
            "is_time_barred": case.is_time_barred,
            "collector_win_rate": case.collector_win_rate,
            "default_risk_score": _get_extra(case, "default_risk_score"),
            "pattern_description": _get_extra(case, "pattern_description"),
        },
    }

    return analysis


def _deterministic_defenses(case: CourtCase) -> list[str]:
    defenses: list[str] = []

    if case.is_time_barred is True:
        defenses.append(
            "Statute of limitations may apply because this debt appears older than Texas's four-year consumer debt window."
        )
    elif case.is_time_barred is False:
        defenses.append(
            "The debt appears within the limitations period, so check other defenses carefully."
        )

    collector_win_rate = case.collector_win_rate
    if collector_win_rate is not None and collector_win_rate >= 0.85:
        defenses.append(
            "Debt ownership proof matters because this collector has a high unopposed win rate."
        )
    elif collector_win_rate is not None and collector_win_rate >= 0.60:
        defenses.append(
            "Ask for proof that the plaintiff owns the debt and that the amount is correct."
        )

    if case.amount_claimed is None:
        defenses.append(
            "Amount dispute may be important because the claim amount is missing from the parsed record."
        )

    pattern_description = _get_extra(case, "pattern_description")
    if pattern_description:
        defenses.append(f"Pattern signal to review: {pattern_description}")

    default_risk_score = _get_extra(case, "default_risk_score")
    if _is_high_risk(default_risk_score):
        defenses.append(
            "Default risk is high, so filing an Answer quickly is the most important next step."
        )

    if case.days_remaining is not None and case.days_remaining <= 7:
        defenses.append(
            "Deadline urgency is high. Do not wait to file an Answer or contact legal aid."
        )

    return _dedupe(defenses)


def _urgency_note(case: CourtCase) -> str:
    if case.days_remaining is None:
        return "Deadline not calculated yet. Check the court docket before advising next steps."

    if case.days_remaining < 0:
        return (
            f"The response deadline may have passed {-case.days_remaining} day(s) ago. "
            "Contact legal aid immediately."
        )

    if case.days_remaining <= 3:
        return (
            f"Critical: about {case.days_remaining} day(s) remain before the response deadline."
        )

    if case.days_remaining <= 7:
        return (
            f"Urgent: about {case.days_remaining} day(s) remain before the response deadline."
        )

    if case.days_remaining <= 14:
        return (
            f"Warning: about {case.days_remaining} day(s) remain before the response deadline."
        )

    return f"Monitor: about {case.days_remaining} day(s) remain before the response deadline."


def _plain_language_summary(case: CourtCase, strongest_defense: str) -> str:
    deadline = (
        f" The response deadline is {_date_to_str(case.deadline_date)}."
        if case.deadline_date
        else ""
    )
    amount = (
        f" The claim amount is ${case.amount_claimed}."
        if case.amount_claimed is not None
        else ""
    )

    return (
        f"{case.plaintiff} filed case {case.case_number} against {case.defendant} "
        f"in {case.county.title()} County.{deadline}{amount} "
        f"Key issue to review: {strongest_defense} "
        "This is legal information, not legal advice."
    )


def _optional_openai_analysis(
    case: CourtCase, deterministic: dict[str, Any]
) -> dict[str, Any] | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None

    try:
        from openai import OpenAI
    except Exception as exc:
        print(f"[case_analyzer] OpenAI package unavailable: {exc}")
        return None

    try:
        client = OpenAI()
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            instructions=SYSTEM_PROMPT,
            input=json.dumps(
                {
                    "case": _case_payload(case),
                    "deterministic_analysis": deterministic,
                },
                default=str,
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "txalert_case_analysis",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "defenses": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "strongest_defense": {"type": "string"},
                            "urgency_note": {"type": "string"},
                            "plain_language_summary": {"type": "string"},
                        },
                        "required": [
                            "defenses",
                            "strongest_defense",
                            "urgency_note",
                            "plain_language_summary",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            max_output_tokens=700,
        )
        return _parse_json_response(response)
    except Exception as exc:
        print(f"[case_analyzer] OpenAI analysis skipped: {exc}")
        return None


def _case_payload(case: CourtCase) -> dict[str, Any]:
    return {
        "id": case.id,
        "case_number": case.case_number,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "filing_date": _date_to_str(case.filing_date),
        "court_type": case.court_type,
        "county": case.county,
        "case_type": case.case_type,
        "amount_claimed": _decimal_to_float(case.amount_claimed),
        "deadline_date": _date_to_str(case.deadline_date),
        "days_remaining": case.days_remaining,
        "is_time_barred": case.is_time_barred,
        "collector_win_rate": case.collector_win_rate,
        "default_risk_score": _get_extra(case, "default_risk_score"),
        "pattern_description": _get_extra(case, "pattern_description"),
    }


def _parse_json_response(response: Any) -> dict[str, Any] | None:
    text = getattr(response, "output_text", None)
    if not text:
        text = _extract_output_text(response)

    if not text:
        return None

    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        return None

    return {
        "defenses": _as_string_list(parsed.get("defenses")),
        "strongest_defense": str(parsed.get("strongest_defense") or ""),
        "urgency_note": str(parsed.get("urgency_note") or ""),
        "plain_language_summary": str(parsed.get("plain_language_summary") or ""),
    }


def _extract_output_text(response: Any) -> str | None:
    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return None

    chunks: list[str] = []
    for item in output:
        content = getattr(item, "content", None)
        if not isinstance(content, list):
            continue
        for part in content:
            text = getattr(part, "text", None)
            if text:
                chunks.append(str(text))

    return "".join(chunks) if chunks else None


def _merge_analysis(
    deterministic: dict[str, Any], llm_analysis: dict[str, Any]
) -> dict[str, Any]:
    merged = dict(deterministic)
    merged["defenses"] = _dedupe(
        _as_string_list(llm_analysis.get("defenses"))
        + _as_string_list(deterministic.get("defenses"))
    )

    for key in ("strongest_defense", "urgency_note", "plain_language_summary"):
        value = llm_analysis.get(key)
        if value:
            merged[key] = value

    merged["llm_enhanced"] = True
    return merged


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [str(item) for item in value if str(item).strip()]


def _is_high_risk(value: Any) -> bool:
    try:
        return float(value) >= 80
    except (TypeError, ValueError):
        return False


def _get_extra(case: CourtCase, field_name: str) -> Any:
    return getattr(case, field_name, None)


def _date_to_str(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _decimal_to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        clean_value = value.strip()
        key = clean_value.lower()
        if not clean_value or key in seen:
            continue

        seen.add(key)
        result.append(clean_value)

    return result
