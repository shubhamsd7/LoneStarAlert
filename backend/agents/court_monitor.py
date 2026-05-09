"""Autonomous court monitoring agent.

This cycle helps legal aid organizations check public court records for their
clients, similar to a paralegal doing a bounded morning review.
"""

from __future__ import annotations

import asyncio
import os
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from importlib import import_module
from typing import Any
from uuid import uuid4

from supabase import Client, create_client

from backend.layer1_entity.entity_resolver import resolve_entity_sync
from backend.models.case import CourtCase, WatchEntry
from backend.services import court_scraper, deadline_calculator


MAX_WATCH_ENTRIES_PER_CYCLE = 10
COUNTY_QUERY_DELAY_SECONDS = 2
WATCH_ENTRIES_TABLE = "watch_entries"
COURT_CASES_TABLE = "court_cases"


supabase_client: Client | None = None


async def run_monitor_cycle() -> list[CourtCase]:
    """Run one bounded public-record monitoring cycle."""
    cycle_started_at = datetime.now(timezone.utc)
    print(f"[court_monitor] cycle started at {cycle_started_at.isoformat()}")

    new_cases: list[CourtCase] = []

    try:
        client = _get_supabase_client()
        watch_entries = _load_watch_entries(client)
        print(f"[court_monitor] loaded {len(watch_entries)} watch entries")
    except Exception as exc:
        print(f"[court_monitor] failed to load watch entries: {exc}")
        print(f"[court_monitor] cycle ended at {datetime.now(timezone.utc).isoformat()}")
        return []

    for watch_entry in watch_entries:
        print(
            "[court_monitor] checking "
            f"{watch_entry.type} watch {watch_entry.id} in {watch_entry.county}"
        )

        try:
            search_results = await _search_watch_entry(watch_entry)
            print(
                "[court_monitor] found "
                f"{len(search_results)} raw results for watch {watch_entry.id}"
            )

            for result in search_results:
                case_number = str(result.get("case_number") or "").strip()
                if not case_number:
                    print("[court_monitor] skipping result with no case number")
                    continue

                if _case_exists(client, case_number):
                    print(f"[court_monitor] skipping duplicate case {case_number}")
                    continue

                court_case = _build_court_case(client, watch_entry, result)
                _save_court_case(client, court_case)
                new_cases.append(court_case)
                print(f"[court_monitor] saved new case {court_case.case_number}")
        except Exception as exc:
            print(f"[court_monitor] watch {watch_entry.id} failed: {exc}")

        await asyncio.sleep(COUNTY_QUERY_DELAY_SECONDS)

    cycle_ended_at = datetime.now(timezone.utc)
    print(
        "[court_monitor] cycle ended at "
        f"{cycle_ended_at.isoformat()} with {len(new_cases)} new cases"
    )
    return new_cases


def _get_supabase_client() -> Client:
    global supabase_client

    if supabase_client is not None:
        return supabase_client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    supabase_client = create_client(supabase_url, supabase_key)
    return supabase_client


def _load_watch_entries(client: Client) -> list[WatchEntry]:
    try:
        response = (
            client.table(WATCH_ENTRIES_TABLE)
            .select("*")
            .eq("status", "active")
            .limit(MAX_WATCH_ENTRIES_PER_CYCLE)
            .execute()
        )
    except Exception as exc:
        print(f"[court_monitor] active watch query failed, falling back: {exc}")
        response = (
            client.table(WATCH_ENTRIES_TABLE)
            .select("*")
            .limit(MAX_WATCH_ENTRIES_PER_CYCLE)
            .execute()
        )

    watch_entries: list[WatchEntry] = []
    for item in response.data or []:
        if isinstance(item, dict) and item.get("status", "active") != "active":
            continue

        try:
            watch_entries.append(WatchEntry.model_validate(item))
        except Exception as exc:
            watch_id = item.get("id", "unknown") if isinstance(item, dict) else "unknown"
            print(f"[court_monitor] skipping invalid watch entry {watch_id}: {exc}")

    return watch_entries


async def _search_watch_entry(watch_entry: WatchEntry) -> list[dict]:
    if watch_entry.type == "address":
        return await court_scraper.search_cases_by_address(
            watch_entry.value, county=watch_entry.county
        )

    return await court_scraper.search_cases_by_name(
        watch_entry.value, county=watch_entry.county
    )


def _case_exists(client: Client, case_number: str) -> bool:
    response = (
        client.table(COURT_CASES_TABLE)
        .select("id")
        .eq("case_number", case_number)
        .limit(1)
        .execute()
    )

    return bool(response.data)


def _build_court_case(
    client: Client, watch_entry: WatchEntry, result: dict[str, Any]
) -> CourtCase:
    filing_date = _parse_date(result.get("filing_date")) or date.today()
    court_type = _normalize_court_type(result.get("court_type"))
    deadline = _calculate_deadline(filing_date, court_type)
    entity = _resolve_entity(result)
    enrichment = _optional_enrichment(
        client,
        watch_entry,
        result,
        filing_date=filing_date,
        court_type=court_type,
        deadline=deadline,
        entity=entity,
    )

    return CourtCase(
        id=str(uuid4()),
        watch_id=watch_entry.id,
        case_number=str(result.get("case_number") or ""),
        plaintiff=str(result.get("plaintiff") or "Unknown plaintiff"),
        defendant=str(result.get("defendant") or watch_entry.value),
        filing_date=filing_date,
        court_type=court_type,
        county=watch_entry.county,
        case_type=str(result.get("case_type") or "Civil"),
        amount_claimed=_parse_decimal(result.get("amount_claimed")),
        deadline_date=deadline.get("deadline_date"),
        days_remaining=deadline.get("days_remaining"),
        is_time_barred=enrichment.get("is_time_barred"),
        collector_win_rate=enrichment.get("collector_win_rate"),
        resolved_entity_id=entity.get("entity_id"),
        canonical_entity_name=entity.get("canonical_name"),
        entity_confidence_score=entity.get("confidence_score"),
        entity_graph={
            "parent_company": entity.get("parent_company"),
            "subsidiaries": entity.get("subsidiaries", []),
        },
        default_risk_score=enrichment.get("default_risk_score"),
        risk_confidence=enrichment.get("risk_confidence"),
        plaintiff_strength=enrichment.get("plaintiff_strength"),
        alert_importance=enrichment.get("alert_importance"),
        pattern_description=enrichment.get("pattern_description"),
        pattern_severity=enrichment.get("pattern_severity"),
        anomaly_score=enrichment.get("anomaly_score"),
        status="active",
    )


def _calculate_deadline(filing_date: date, court_type: Any) -> dict[str, Any]:
    calculate_deadline = getattr(deadline_calculator, "calculate_deadline", None)
    if calculate_deadline is None:
        return {"deadline_date": None, "days_remaining": None}

    try:
        result = calculate_deadline(filing_date, _normalize_court_type(court_type))
    except Exception as exc:
        print(f"[court_monitor] deadline calculation failed: {exc}")
        return {"deadline_date": None, "days_remaining": None}

    if isinstance(result, dict):
        return {
            "deadline_date": _parse_date(result.get("deadline_date")),
            "days_remaining": result.get("days_remaining"),
            "urgency_level": result.get("urgency_level") or result.get("urgency"),
        }

    return {
        "deadline_date": _parse_date(getattr(result, "deadline_date", None)),
        "days_remaining": getattr(result, "days_remaining", None),
        "urgency_level": getattr(result, "urgency_level", None)
        or getattr(result, "urgency", None),
    }


def _optional_enrichment(
    client: Client,
    watch_entry: WatchEntry,
    result: dict[str, Any],
    filing_date: date,
    court_type: str,
    deadline: dict[str, Any],
    entity: dict[str, Any],
) -> dict[str, Any]:
    enrichment: dict[str, Any] = {
        "is_time_barred": None,
        "collector_win_rate": None,
        "default_risk_score": None,
        "risk_confidence": None,
        "plaintiff_strength": None,
        "alert_importance": None,
        "pattern_description": None,
        "pattern_severity": None,
        "anomaly_score": None,
    }

    _try_limitations_enrichment(enrichment, result)
    historical_cases = _load_historical_cases(
        client,
        plaintiff=str(result.get("plaintiff") or ""),
        county=watch_entry.county,
    )
    _try_collector_enrichment(enrichment, result, historical_cases)
    _try_future_layer_enrichment(
        enrichment,
        result,
        historical_cases,
        filing_date=filing_date,
        court_type=court_type,
        deadline=deadline,
        entity=entity,
    )

    return enrichment


def _try_limitations_enrichment(
    enrichment: dict[str, Any], result: dict[str, Any]
) -> None:
    debt_origin_date = _parse_date(
        result.get("debt_origin_date")
        or result.get("debt_date")
        or result.get("last_payment_date")
    )
    if debt_origin_date is None:
        return

    checker = _load_optional_callable(
        "backend.services.limitations_checker",
        "check_statute_of_limitations",
    )
    if checker is None:
        print("[court_monitor] limitations_checker unavailable; skipping")
        return

    try:
        limitations = checker(
            debt_origin_date,
            str(result.get("debt_type") or "unknown"),
            _parse_date(result.get("last_payment_date")),
        )
        enrichment["is_time_barred"] = _read_value(limitations, "is_time_barred")
        print("[court_monitor] limitations enrichment complete")
    except Exception as exc:
        print(f"[court_monitor] limitations enrichment failed: {exc}")


def _try_collector_enrichment(
    enrichment: dict[str, Any], result: dict[str, Any], historical_cases: list[dict]
) -> None:
    if not historical_cases:
        print("[court_monitor] no collector history available; skipping")
        return

    scorer = _load_optional_callable(
        "backend.services.collector_scorer",
        "score_collector",
    )
    if scorer is None:
        print("[court_monitor] collector_scorer unavailable; skipping")
        return

    try:
        plaintiff_name = str(result.get("plaintiff") or "")
        profile = scorer(plaintiff_name, historical_cases)

        enrichment["collector_win_rate"] = _read_value(
            profile,
            "default_win_rate",
            "win_rate",
        )
        print("[court_monitor] collector enrichment complete")
    except Exception as exc:
        print(f"[court_monitor] collector enrichment failed: {exc}")


def _try_future_layer_enrichment(
    enrichment: dict[str, Any],
    result: dict[str, Any],
    historical_cases: list[dict],
    filing_date: date,
    court_type: str,
    deadline: dict[str, Any],
    entity: dict[str, Any],
) -> None:
    risk_scorer = _load_optional_callable("backend.layer2_risk.risk_model", "score_risk")
    pattern_detector = _load_optional_callable(
        "backend.layer3_patterns.pattern_detector",
        "detect_patterns",
    )

    if risk_scorer is None:
        print("[court_monitor] risk_model unavailable; skipping")
    else:
        try:
            risk = risk_scorer(
                {
                    **result,
                    "resolved_entity_id": entity.get("entity_id"),
                    "canonical_entity_name": entity.get("canonical_name"),
                    "entity_confidence_score": entity.get("confidence_score"),
                    "filing_date": filing_date,
                    "court_type": court_type,
                    "days_remaining": deadline.get("days_remaining"),
                    "is_time_barred": enrichment.get("is_time_barred"),
                    "collector_win_rate": enrichment.get("collector_win_rate"),
                }
            )
            enrichment["default_risk_score"] = _read_value(risk, "default_risk_score")
            enrichment["risk_confidence"] = _read_value(risk, "risk_confidence")
            enrichment["plaintiff_strength"] = _read_value(risk, "plaintiff_strength")
            enrichment["alert_importance"] = _read_value(risk, "alert_importance")
            print("[court_monitor] risk enrichment complete")
        except Exception as exc:
            print(f"[court_monitor] risk enrichment failed: {exc}")

    if pattern_detector is None:
        print("[court_monitor] pattern_detector unavailable; skipping")
    elif not historical_cases:
        print("[court_monitor] pattern_detector needs case history; skipping")
    else:
        try:
            pattern_result = pattern_detector(
                [
                    *historical_cases,
                    {
                        **result,
                        "resolved_entity_id": entity.get("entity_id"),
                        "plaintiff": entity.get("canonical_name")
                        or result.get("plaintiff"),
                    },
                ]
            )
            enrichment["pattern_description"] = _read_value(
                pattern_result, "pattern_description"
            )
            enrichment["pattern_severity"] = _read_value(
                pattern_result, "pattern_severity"
            )
            enrichment["anomaly_score"] = _read_value(pattern_result, "anomaly_score")
            print("[court_monitor] pattern enrichment complete")
        except Exception as exc:
            print(f"[court_monitor] pattern enrichment failed: {exc}")


def _resolve_entity(result: dict[str, Any]) -> dict[str, Any]:
    try:
        entity = resolve_entity_sync(
            str(result.get("plaintiff") or ""),
            str(result.get("case_type") or ""),
        )
        print(
            "[court_monitor] entity resolution complete: "
            f"{entity.get('canonical_name')} ({entity.get('confidence_score')})"
        )
        return entity
    except Exception as exc:
        print(f"[court_monitor] entity resolution failed: {exc}")
        return {
            "entity_id": None,
            "canonical_name": str(result.get("plaintiff") or ""),
            "confidence_score": 0.0,
            "subsidiaries": [],
            "parent_company": None,
        }


def _load_historical_cases(client: Client, plaintiff: str, county: str) -> list[dict]:
    if not plaintiff:
        return []

    try:
        response = (
            client.table(COURT_CASES_TABLE)
            .select("*")
            .eq("plaintiff", plaintiff)
            .eq("county", county)
            .limit(100)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        print(f"[court_monitor] failed to load collector history: {exc}")
        return []


def _load_optional_callable(module_name: str, callable_name: str) -> Any | None:
    try:
        module = import_module(module_name)
    except ModuleNotFoundError:
        return None
    except Exception as exc:
        print(f"[court_monitor] optional module {module_name} failed to load: {exc}")
        return None

    candidate = getattr(module, callable_name, None)
    if callable(candidate):
        return candidate

    return None


def _read_value(source: Any, *names: str) -> Any:
    for name in names:
        if isinstance(source, dict) and name in source:
            return source[name]
        if hasattr(source, name):
            return getattr(source, name)

    return None


def _save_court_case(client: Client, court_case: CourtCase) -> None:
    client.table(COURT_CASES_TABLE).insert(
        court_case.model_dump(mode="json")
    ).execute()


def _normalize_court_type(value: Any) -> str:
    court_type = str(value or "").lower()
    if court_type == "justice" or "justice" in court_type or "jp" in court_type:
        return "justice"

    return "district"


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value

    if not value:
        return None

    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _parse_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value).replace("$", "").replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return None
