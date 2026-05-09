"""FastAPI entry point for TxAlert."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Literal
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import Client

from backend.agents import case_analyzer, court_monitor
from backend.models.case import Alert, CourtCase, WatchEntry


load_dotenv()


WATCH_ENTRIES_TABLE = "watch_entries"
COURT_CASES_TABLE = "court_cases"
ALERTS_TABLE = "alerts"
MONITOR_INTERVAL_SECONDS = 86400


background_monitor_task: asyncio.Task | None = None


app = FastAPI(
    title="TxAlert API",
    description="Autonomous public court-record monitoring for Texas legal aid workflows.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WatchRequest(BaseModel):
    type: Literal["name", "address"]
    value: str = Field(min_length=1)
    county: str = Field(min_length=1)
    email: str = Field(min_length=3)


class WatchResponse(BaseModel):
    id: str
    watch_id: str
    type: Literal["name", "address"]
    value: str
    county: str
    email: str
    createdAt: str
    cases_found: int
    message: str


class CheckNowResponse(BaseModel):
    new_cases: int
    cases: list[dict[str, Any]]


class DeleteWatchResponse(BaseModel):
    success: bool


@app.post("/watch", response_model=WatchResponse)
async def create_watch(request: WatchRequest) -> WatchResponse:
    """Create a watch entry and immediately check public court records."""
    client = _get_client_or_503()
    watch_entry = _save_watch_entry(client, request)
    new_cases = await _run_check_for_watch(client, watch_entry)

    return _watch_response(
        watch_entry,
        cases_found=len(new_cases),
        message=(
            f"Watching for {request.type} matches in {request.county}. "
            f"Found {len(new_cases)} new case(s) in the first check."
        ),
    )


@app.post("/watches", response_model=WatchResponse)
async def create_watch_frontend_alias(request: WatchRequest) -> WatchResponse:
    """Frontend-compatible alias for creating a watch entry."""
    return await create_watch(request)


@app.get("/alerts/{email}")
async def get_alerts_for_email_path(email: str) -> list[dict[str, Any]]:
    """Return active case alerts for an email address."""
    return _get_alerts_for_email(str(email))


@app.get("/alerts")
async def get_alerts_for_email_query(
    email: str = Query(..., min_length=3),
) -> list[dict[str, Any]]:
    """Frontend-compatible alerts route using an email query string."""
    return _get_alerts_for_email(str(email))


@app.post("/check-now/{watch_id}", response_model=CheckNowResponse)
async def check_now(watch_id: str) -> CheckNowResponse:
    """Run one immediate public-record check for a single watch entry."""
    client = _get_client_or_503()
    watch_entry = _load_watch_entry(client, watch_id)
    new_cases = await _run_check_for_watch(client, watch_entry)

    return CheckNowResponse(
        new_cases=len(new_cases),
        cases=[_case_alert_payload(case) for case in new_cases],
    )


@app.post("/watches/{watch_id}/check")
async def check_now_frontend_alias(watch_id: str) -> list[dict[str, Any]]:
    """Frontend-compatible check-now route."""
    response = await check_now(watch_id)
    return response.cases


@app.delete("/watch/{watch_id}", response_model=DeleteWatchResponse)
async def delete_watch(watch_id: str) -> DeleteWatchResponse:
    """Deactivate a watch entry."""
    client = _get_client_or_503()
    _deactivate_watch_entry(client, watch_id)
    return DeleteWatchResponse(success=True)


@app.delete("/watches/{watch_id}", response_model=DeleteWatchResponse)
async def delete_watch_frontend_alias(watch_id: str) -> DeleteWatchResponse:
    """Frontend-compatible watch deletion route."""
    return await delete_watch(watch_id)


@app.get("/health")
async def health() -> dict[str, str]:
    """Basic health check for demos and uptime probes."""
    monitor_state = (
        "running"
        if background_monitor_task and not background_monitor_task.done()
        else "stopped"
    )
    return {"status": "ok", "monitor": monitor_state}


@app.on_event("startup")
async def start_background_monitor() -> None:
    """Start the daily monitor loop when FastAPI starts."""
    global background_monitor_task

    if background_monitor_task and not background_monitor_task.done():
        return

    background_monitor_task = asyncio.create_task(_daily_monitor_loop())
    print("[background] daily monitor task scheduled")


async def _daily_monitor_loop() -> None:
    """Run monitor, analysis, alerts, and Miro updates every 24 hours."""
    while True:
        cycle_started_at = datetime.now(timezone.utc)
        print(f"[background] cycle started at {cycle_started_at.isoformat()}")

        try:
            client = court_monitor._get_supabase_client()
            new_cases = await court_monitor.run_monitor_cycle()
            print(f"[background] monitor found {len(new_cases)} new case(s)")

            for court_case in new_cases:
                await _process_new_case_alert(client, court_case)
        except Exception as exc:
            print(f"[background] cycle failed: {exc}")

        cycle_ended_at = datetime.now(timezone.utc)
        print(f"[background] cycle ended at {cycle_ended_at.isoformat()}")
        await asyncio.sleep(MONITOR_INTERVAL_SECONDS)


async def _process_new_case_alert(client: Client, court_case: CourtCase) -> None:
    """Analyze a case, generate an alert, save it, and update Miro if possible."""
    try:
        if _alert_exists(client, court_case.id):
            print(f"[background] alert already exists for {court_case.case_number}")
            return

        analysis = case_analyzer.analyze_case(court_case)
        alert = _generate_alert(court_case, analysis)
        _save_alert(client, alert)
        frame_url = await _create_miro_board(court_case, alert)

        if frame_url:
            alert.miro_board_url = frame_url
            _save_miro_board_url(client, alert.id, frame_url)
            print(
                f"[background] Miro board created for {court_case.case_number}: {frame_url}"
            )

        _log_email_alert(court_case, alert)
    except Exception as exc:
        print(f"[background] alert pipeline failed for {court_case.case_number}: {exc}")


def _get_client_or_503() -> Client:
    try:
        return court_monitor._get_supabase_client()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Supabase is not configured: {exc}",
        ) from exc


def _generate_alert(court_case: CourtCase, analysis: dict[str, Any]) -> Alert:
    generator = _load_optional_callable(
        "backend.agents.alert_generator",
        "generate_alert",
    )

    if generator is not None:
        try:
            generated = generator(court_case, analysis)
            if isinstance(generated, Alert):
                return generated
            if isinstance(generated, dict):
                return Alert.model_validate(generated)
        except Exception as exc:
            print(f"[background] alert_generator failed, using fallback: {exc}")

    return _fallback_alert(court_case, analysis)


def _fallback_alert(court_case: CourtCase, analysis: dict[str, Any]) -> Alert:
    message = analysis.get("plain_language_summary") or (
        f"{court_case.plaintiff} filed case {court_case.case_number}. "
        "Check the deadline and contact legal aid."
    )

    return Alert(
        id=str(uuid4()),
        case_id=court_case.id,
        message=str(message),
        answer_form_url=None,
        legal_aid=[],
        sent_at=datetime.now(timezone.utc),
    )


def _save_alert(client: Client, alert: Alert) -> None:
    try:
        client.table(ALERTS_TABLE).insert(
            alert.model_dump(mode="json", exclude_none=True)
        ).execute()
        print(f"[background] saved alert {alert.id} for case {alert.case_id}")
    except Exception as exc:
        print(f"[background] failed to save alert {alert.id}: {exc}")


def _save_miro_board_url(client: Client, alert_id: str, frame_url: str) -> None:
    try:
        (
            client.table(ALERTS_TABLE)
            .update({"miro_board_url": frame_url})
            .eq("id", alert_id)
            .execute()
        )
    except Exception as exc:
        print(f"[background] failed to save Miro URL for alert {alert_id}: {exc}")


def _alert_exists(client: Client, case_id: str) -> bool:
    try:
        response = (
            client.table(ALERTS_TABLE)
            .select("id")
            .eq("case_id", case_id)
            .limit(1)
            .execute()
        )
        return bool(response.data)
    except Exception as exc:
        print(f"[background] failed to check existing alerts: {exc}")
        return False


async def _create_miro_board(court_case: CourtCase, alert: Alert) -> str:
    create_case_board = _load_optional_callable(
        "backend.services.miro_service",
        "create_case_board",
    )
    if create_case_board is None:
        print("[background] miro_service unavailable; skipping board update")
        return ""

    try:
        result = create_case_board(court_case, alert)
        if hasattr(result, "__await__"):
            result = await result
        return str(result or "")
    except Exception as exc:
        print(f"[background] Miro update failed: {exc}")
        return ""


def _log_email_alert(court_case: CourtCase, alert: Alert) -> None:
    print(
        "[email-log] "
        f"case={court_case.case_number} alert={alert.id} message={alert.message}"
    )


def _load_optional_callable(module_name: str, callable_name: str) -> Any | None:
    try:
        module = import_module(module_name)
    except ModuleNotFoundError:
        return None
    except Exception as exc:
        print(f"[background] optional module {module_name} failed to load: {exc}")
        return None

    candidate = getattr(module, callable_name, None)
    return candidate if callable(candidate) else None


def _save_watch_entry(client: Client, request: WatchRequest) -> WatchEntry:
    created_at = datetime.now(timezone.utc)
    payload = {
        "id": str(uuid4()),
        "type": request.type,
        "value": request.value.strip(),
        "county": request.county.lower().strip(),
        "user_email": str(request.email),
        "created_at": created_at.isoformat(),
        "status": "active",
    }

    try:
        response = client.table(WATCH_ENTRIES_TABLE).insert(payload).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not create watch entry: {exc}",
        ) from exc

    saved = (response.data or [payload])[0]
    return WatchEntry.model_validate(saved)


def _load_watch_entry(client: Client, watch_id: str) -> WatchEntry:
    try:
        response = (
            client.table(WATCH_ENTRIES_TABLE)
            .select("*")
            .eq("id", watch_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load watch entry: {exc}",
        ) from exc

    if not response.data:
        raise HTTPException(status_code=404, detail="Watch entry not found")

    record = response.data[0]
    if record.get("status", "active") != "active":
        raise HTTPException(status_code=404, detail="Watch entry is not active")

    return WatchEntry.model_validate(record)


async def _run_check_for_watch(
    client: Client, watch_entry: WatchEntry
) -> list[CourtCase]:
    print(f"[api] running immediate check for watch {watch_entry.id}")
    new_cases: list[CourtCase] = []

    try:
        search_results = await court_monitor._search_watch_entry(watch_entry)
    except Exception as exc:
        print(f"[api] watch {watch_entry.id} search failed: {exc}")
        return []

    for result in search_results:
        case_number = str(result.get("case_number") or "").strip()
        if not case_number:
            print("[api] skipping result with no case number")
            continue

        try:
            if court_monitor._case_exists(client, case_number):
                print(f"[api] skipping duplicate case {case_number}")
                continue

            court_case = court_monitor._build_court_case(client, watch_entry, result)
            court_monitor._save_court_case(client, court_case)
            new_cases.append(court_case)
            print(f"[api] saved new case {court_case.case_number}")
        except Exception as exc:
            print(f"[api] failed to save case {case_number}: {exc}")

    return new_cases


def _deactivate_watch_entry(client: Client, watch_id: str) -> None:
    try:
        response = (
            client.table(WATCH_ENTRIES_TABLE)
            .update({"status": "inactive"})
            .eq("id", watch_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not deactivate watch entry: {exc}",
        ) from exc

    if response.data == []:
        raise HTTPException(status_code=404, detail="Watch entry not found")


def _get_alerts_for_email(email: str) -> list[dict[str, Any]]:
    client = _get_client_or_503()
    watches = _load_watches_for_email(client, email)
    if not watches:
        return []

    watch_ids = [watch["id"] for watch in watches if watch.get("id")]
    if not watch_ids:
        return []

    cases = _load_cases_for_watch_ids(client, watch_ids)
    alerts = _load_alerts_for_cases(client, [case.get("id") for case in cases])
    alerts_by_case_id = {
        alert.get("case_id"): alert for alert in alerts if alert.get("case_id")
    }

    return [
        _case_alert_payload(
            CourtCase.model_validate(case),
            alert=alerts_by_case_id.get(case.get("id")),
        )
        for case in cases
    ]


def _load_watches_for_email(client: Client, email: str) -> list[dict[str, Any]]:
    try:
        response = (
            client.table(WATCH_ENTRIES_TABLE)
            .select("*")
            .eq("user_email", email)
            .execute()
        )
        return [
            item
            for item in response.data or []
            if item.get("status", "active") == "active"
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load watch entries: {exc}",
        ) from exc


def _load_cases_for_watch_ids(client: Client, watch_ids: list[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    for watch_id in watch_ids:
        try:
            response = (
                client.table(COURT_CASES_TABLE)
                .select("*")
                .eq("watch_id", watch_id)
                .execute()
            )
            cases.extend(
                item
                for item in response.data or []
                if item.get("status", "active") in {"active", "alerted"}
            )
        except Exception as exc:
            print(f"[api] failed to load cases for watch {watch_id}: {exc}")

    cases.sort(key=lambda item: item.get("days_remaining") or 9999)
    return cases


def _load_alerts_for_cases(
    client: Client, case_ids: list[str | None]
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    for case_id in [case_id for case_id in case_ids if case_id]:
        try:
            response = (
                client.table(ALERTS_TABLE)
                .select("*")
                .eq("case_id", case_id)
                .limit(1)
                .execute()
            )
            alerts.extend(response.data or [])
        except Exception as exc:
            print(f"[api] failed to load alert for case {case_id}: {exc}")

    return alerts


def _watch_response(
    watch_entry: WatchEntry, cases_found: int, message: str
) -> WatchResponse:
    return WatchResponse(
        id=watch_entry.id,
        watch_id=watch_entry.id,
        type=watch_entry.type,
        value=watch_entry.value,
        county=watch_entry.county.title(),
        email=watch_entry.user_email,
        createdAt=watch_entry.created_at.isoformat(),
        cases_found=cases_found,
        message=message,
    )


def _case_alert_payload(
    court_case: CourtCase, alert: dict[str, Any] | None = None
) -> dict[str, Any]:
    days_remaining = court_case.days_remaining
    return {
        "id": court_case.id,
        "watchId": court_case.watch_id,
        "caseNumber": court_case.case_number,
        "filingDate": court_case.filing_date.isoformat(),
        "plaintiff": court_case.plaintiff,
        "defendant": court_case.defendant,
        "county": court_case.county.title(),
        "amount": float(court_case.amount_claimed)
        if court_case.amount_claimed is not None
        else None,
        "deadlineDate": court_case.deadline_date.isoformat()
        if court_case.deadline_date
        else None,
        "daysRemaining": days_remaining,
        "urgency": _urgency_from_days(days_remaining),
        "limitationsStatus": _limitations_status(court_case.is_time_barred),
        "collectorWinRate": court_case.collector_win_rate,
        "defaultRiskScore": _get_extra(court_case, "default_risk_score"),
        "riskConfidence": _get_extra(court_case, "risk_confidence"),
        "plaintiffStrength": _get_extra(court_case, "plaintiff_strength"),
        "alertImportance": _get_extra(court_case, "alert_importance"),
        "pattern": _pattern_payload(court_case),
        "answerText": alert.get("message") if alert else None,
        "miroBoardUrl": alert.get("miro_board_url") if alert else None,
        "legalAid": alert.get("legal_aid") if alert else [],
    }


def _urgency_from_days(days_remaining: int | None) -> str:
    if days_remaining is None:
        return "MONITOR"
    if days_remaining <= 3:
        return "CRITICAL"
    if days_remaining <= 7:
        return "URGENT"
    if days_remaining <= 14:
        return "WARNING"
    return "MONITOR"


def _limitations_status(is_time_barred: bool | None) -> str | None:
    if is_time_barred is None:
        return None
    if is_time_barred:
        return "May be time-barred"
    return "Within limitation period"


def _pattern_payload(court_case: CourtCase) -> dict[str, Any] | None:
    description = _get_extra(court_case, "pattern_description")
    if not description:
        return None

    return {
        "severity": _get_extra(court_case, "pattern_severity") or "medium",
        "description": description,
        "anomalyScore": _get_extra(court_case, "anomaly_score"),
    }


def _get_extra(model: BaseModel, field_name: str) -> Any:
    return getattr(model, field_name, None)
