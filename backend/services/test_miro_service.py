from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import httpx

from backend.models.case import Alert, CourtCase
from backend.services import miro_service


def _case() -> CourtCase:
    return CourtCase(
        id="case-1",
        watch_id="watch-1",
        case_number="JP-2026-001",
        plaintiff="Acme Debt LLC",
        defendant="Maria Garcia",
        filing_date=date(2026, 1, 5),
        court_type="justice",
        county="travis",
        case_type="debt",
        amount_claimed=Decimal("1250"),
        deadline_date=date(2026, 1, 19),
        days_remaining=4,
        is_time_barred=False,
        collector_win_rate=0.86,
        default_risk_score=0.82,
        risk_confidence=0.74,
        pattern_description="5 cases were filed on 2026-01-05.",
        pattern_severity="medium",
        anomaly_score=0.67,
        status="active",
    )


def _alert() -> Alert:
    return Alert(
        id="alert-1",
        case_id="case-1",
        message=(
            "Acme Debt LLC filed case JP-2026-001. "
            "Key issue to review: Ask for proof that the plaintiff owns the debt. "
            "This is legal information, not legal advice."
        ),
        sent_at=datetime.now(timezone.utc),
    )


def test_create_case_board_returns_empty_string_without_credentials(monkeypatch) -> None:
    monkeypatch.delenv("MIRO_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("MIRO_BOARD_ID", raising=False)

    assert miro_service.create_case_board(_case(), _alert()) == ""


def test_create_case_board_creates_frame_and_case_stickies(monkeypatch) -> None:
    requests: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = request.read()
        requests.append({"url": str(request.url), "body": payload.decode()})
        if request.url.path.endswith("/frames"):
            return httpx.Response(201, json={"id": "frame-123"})
        return httpx.Response(201, json={"id": "sticky-123"})

    transport = httpx.MockTransport(handler)

    class MockClient(httpx.Client):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setenv("MIRO_ACCESS_TOKEN", "token")
    monkeypatch.setenv("MIRO_BOARD_ID", "board-123")
    monkeypatch.setattr(miro_service.httpx, "Client", MockClient)

    url = miro_service.create_case_board(_case(), _alert())

    assert url == "https://miro.com/app/board/board-123/?moveToWidget=frame-123"
    assert any(request["url"].endswith("/boards/board-123/frames") for request in requests)
    sticky_requests = [
        request for request in requests if request["url"].endswith("/sticky_notes")
    ]
    assert len(sticky_requests) == 6
    assert any('"fillColor":"red"' in request["body"] for request in sticky_requests)
    assert any("Risk + pattern" in request["body"] for request in sticky_requests)
