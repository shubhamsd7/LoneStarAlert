"""Miro board update service."""

from __future__ import annotations

import html
import os
from datetime import date
from decimal import Decimal
from typing import Any
from urllib.parse import quote

import httpx

from backend.models.case import Alert, CourtCase


MIRO_API_BASE = "https://api.miro.com/v2"
FRAME_WIDTH = 1600
FRAME_HEIGHT = 1050


def create_case_board(case: CourtCase, alert: Alert) -> str:
    """Create a Miro case frame and return a direct frame URL.

    The alert pipeline treats Miro as optional. Missing credentials, API
    failures, or schema differences are logged here and converted to an empty
    string so one board failure never blocks the monitoring cycle.
    """
    token = os.getenv("MIRO_ACCESS_TOKEN")
    board_id = os.getenv("MIRO_BOARD_ID")

    if not token or not board_id:
        print("[miro_service] MIRO_ACCESS_TOKEN or MIRO_BOARD_ID not configured")
        return ""

    try:
        with httpx.Client(
            base_url=MIRO_API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=12.0,
        ) as client:
            frame = _create_frame(client, board_id, case)
            frame_id = str(frame.get("id") or "")
            if not frame_id:
                print("[miro_service] frame creation response did not include an id")
                return ""

            _create_case_items(client, board_id, case, alert)
            return _frame_url(board_id, frame_id)
    except Exception as exc:
        print(f"[miro_service] Miro board creation failed: {exc}")
        return ""


def _create_frame(client: httpx.Client, board_id: str, case: CourtCase) -> dict[str, Any]:
    payload = {
        "data": {
            "format": "custom",
            "title": f"TxAlert {case.case_number}",
            "type": "freeform",
        },
        "style": {"fillColor": "#ffffff"},
        "position": {"x": 0, "y": 0},
        "geometry": {"width": FRAME_WIDTH, "height": FRAME_HEIGHT},
    }
    response = client.post(f"/boards/{board_id}/frames", json=payload)
    response.raise_for_status()
    return response.json()


def _create_case_items(
    client: httpx.Client,
    board_id: str,
    case: CourtCase,
    alert: Alert,
) -> None:
    sticky_specs = [
        {
            "content": _case_summary(case),
            "x": -530,
            "y": -360,
            "color": "light_blue",
        },
        {
            "content": _deadline_note(case),
            "x": -40,
            "y": -360,
            "color": "red",
        },
        {
            "content": _timeline_note(case),
            "x": 450,
            "y": -360,
            "color": "light_yellow",
        },
        {
            "content": _checklist_note(),
            "x": -530,
            "y": 80,
            "color": "light_green",
        },
        {
            "content": _defense_note(alert),
            "x": -40,
            "y": 80,
            "color": "light_pink",
        },
    ]

    risk_pattern = _risk_pattern_note(case)
    if risk_pattern:
        sticky_specs.append(
            {
                "content": risk_pattern,
                "x": 450,
                "y": 80,
                "color": "orange",
            }
        )

    for spec in sticky_specs:
        _create_sticky_note(
            client,
            board_id,
            content=spec["content"],
            x=spec["x"],
            y=spec["y"],
            fill_color=spec["color"],
        )


def _create_sticky_note(
    client: httpx.Client,
    board_id: str,
    *,
    content: str,
    x: int,
    y: int,
    fill_color: str,
) -> None:
    payload = {
        "data": {"content": content, "shape": "rectangle"},
        "style": {
            "fillColor": fill_color,
            "textAlign": "left",
            "textAlignVertical": "top",
        },
        "position": {"x": x, "y": y},
    }
    response = client.post(f"/boards/{board_id}/sticky_notes", json=payload)
    response.raise_for_status()


def _case_summary(case: CourtCase) -> str:
    amount = _money(case.amount_claimed)
    return _html_lines(
        [
            _strong(case.case_number),
            f"Plaintiff: {case.plaintiff}",
            f"Defendant: {case.defendant}",
            f"County: {case.county.title()}",
            f"Claim: {amount}",
            "Source: public Texas court record",
        ]
    )


def _deadline_note(case: CourtCase) -> str:
    deadline = _date_text(case.deadline_date)
    days = case.days_remaining
    if days is None:
        countdown = "Deadline pending"
    elif days < 0:
        countdown = f"{abs(days)} day(s) past"
    elif days == 0:
        countdown = "Due today"
    else:
        countdown = f"{days} day(s) left"

    return _html_lines(
        [
            "<strong>Deadline</strong>",
            f"Answer deadline: {deadline}",
            f"Countdown: {countdown}",
            "Confirm service and docket details before action.",
        ]
    )


def _timeline_note(case: CourtCase) -> str:
    return _html_lines(
        [
            "<strong>Timeline</strong>",
            f"Filed: {_date_text(case.filing_date)}",
            f"Deadline: {_date_text(case.deadline_date)}",
            "Hearing: check court docket",
        ]
    )


def _checklist_note() -> str:
    return _html_lines(
        [
            "<strong>Action checklist</strong>",
            "1. Confirm service date.",
            "2. File an Answer before deadline.",
            "3. Ask for proof of debt ownership.",
            "4. Contact legal aid.",
        ]
    )


def _defense_note(alert: Alert) -> str:
    strongest = _strongest_defense(alert.message)
    return _html_lines(
        [
            "<strong>Strongest issue to review</strong>",
            strongest,
            "Legal information only; not legal advice.",
        ]
    )


def _risk_pattern_note(case: CourtCase) -> str:
    lines: list[str] = ["<strong>Risk + pattern</strong>"]

    if case.default_risk_score is not None:
        lines.append(f"Default risk: {_percent(case.default_risk_score)}")
    if case.risk_confidence is not None:
        lines.append(f"Risk confidence: {_percent(case.risk_confidence)}")
    if case.pattern_description:
        severity = case.pattern_severity or "medium"
        lines.append(f"Pattern ({severity}): {case.pattern_description}")
    if case.anomaly_score is not None:
        lines.append(f"Pattern score: {_percent(case.anomaly_score)}")

    return _html_lines(lines) if len(lines) > 1 else ""


def _strongest_defense(message: str) -> str:
    marker = "Key issue to review:"
    if marker in message:
        return message.split(marker, 1)[1].split("This is legal information", 1)[0].strip()
    return message.strip() or "Respond before the deadline and contact legal aid."


def _html_lines(lines: list[str]) -> str:
    escaped: list[str] = []
    for line in lines:
        if line.startswith("<strong>") and line.endswith("</strong>"):
            escaped.append(line)
        else:
            escaped.append(html.escape(line))
    return "<br/>".join(escaped)


def _strong(value: str) -> str:
    return f"<strong>{html.escape(value)}</strong>"


def _date_text(value: date | None) -> str:
    return value.isoformat() if value else "pending"


def _money(value: Decimal | None) -> str:
    if value is None:
        return "not listed"
    return f"${float(value):,.0f}"


def _percent(value: float) -> str:
    return f"{round(value * 100)}%"


def _frame_url(board_id: str, frame_id: str) -> str:
    return f"https://miro.com/app/board/{quote(board_id, safe='=')}/?moveToWidget={quote(frame_id)}"
