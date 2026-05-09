"""Lightweight entity resolver for hackathon-safe collector matching."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any


KNOWN_COLLECTORS: dict[str, dict[str, Any]] = {
    "resurgent_capital": {
        "canonical_name": "Resurgent Capital Services",
        "aliases": [
            "LVNV Funding LLC",
            "LVNV Funding",
            "L.V.N.V.",
            "Resurgent Capital",
            "Resurgent Capital Services",
            "Sherman Originator LLC",
        ],
        "subsidiaries": ["LVNV Funding LLC", "Sherman Originator LLC"],
        "parent_company": "Encore Capital Group",
    },
    "midland_credit": {
        "canonical_name": "Midland Credit Management",
        "aliases": [
            "Midland Credit Management",
            "Midland Funding LLC",
            "Midland Funding",
            "MCM",
        ],
        "subsidiaries": ["Midland Funding LLC"],
        "parent_company": "Encore Capital Group",
    },
    "portfolio_recovery": {
        "canonical_name": "Portfolio Recovery Associates",
        "aliases": [
            "Portfolio Recovery Associates",
            "Portfolio Recovery Associates LLC",
            "PRA Group",
            "PRA III LLC",
        ],
        "subsidiaries": ["Portfolio Recovery Associates LLC", "PRA III LLC"],
        "parent_company": "PRA Group",
    },
    "cavalry": {
        "canonical_name": "Cavalry Portfolio Services",
        "aliases": [
            "Cavalry Portfolio Services",
            "Cavalry SPV I LLC",
            "Cavalry SPV II LLC",
            "Cavalry Investments",
        ],
        "subsidiaries": ["Cavalry SPV I LLC", "Cavalry SPV II LLC"],
        "parent_company": "Cavalry Investments",
    },
    "velocity": {
        "canonical_name": "Velocity Investments",
        "aliases": [
            "Velocity Investments",
            "Velocity Investments LLC",
            "Velocity Portfolio Group",
        ],
        "subsidiaries": ["Velocity Investments LLC"],
        "parent_company": "Velocity Portfolio Group",
    },
}


async def resolve_entity(plaintiff_name: str, case_type: str = "") -> dict[str, Any]:
    """Resolve a plaintiff name to a canonical debt-collector entity.

    The resolver is intentionally bounded and local for the demo. It never calls
    private data sources and never raises for unknown plaintiffs.
    """
    return resolve_entity_sync(plaintiff_name, case_type)


def resolve_entity_sync(plaintiff_name: str, case_type: str = "") -> dict[str, Any]:
    """Synchronous resolver used by the monitor pipeline."""
    raw_name = str(plaintiff_name or "").strip()
    if not raw_name:
        return _unknown_result(raw_name, case_type)

    best_entity_id: str | None = None
    best_score = 0.0
    normalized_name = _normalize(raw_name)

    for entity_id, profile in KNOWN_COLLECTORS.items():
        for alias in profile["aliases"]:
            score = _match_score(normalized_name, _normalize(alias))
            if score > best_score:
                best_entity_id = entity_id
                best_score = score

    if best_entity_id is None or best_score < 0.72:
        return _unknown_result(raw_name, case_type)

    profile = KNOWN_COLLECTORS[best_entity_id]
    return {
        "entity_id": best_entity_id,
        "canonical_name": profile["canonical_name"],
        "confidence_score": round(best_score, 2),
        "subsidiaries": profile["subsidiaries"],
        "parent_company": profile["parent_company"],
        "case_type": case_type,
    }


def _unknown_result(plaintiff_name: str, case_type: str) -> dict[str, Any]:
    return {
        "entity_id": None,
        "canonical_name": plaintiff_name,
        "confidence_score": 0.0,
        "subsidiaries": [],
        "parent_company": None,
        "case_type": case_type,
    }


def _match_score(left: str, right: str) -> float:
    if not left or not right:
        return 0.0

    if left == right:
        return 1.0

    if left in right or right in left:
        return 0.90

    left_tokens = set(left.split())
    right_tokens = set(right.split())
    overlap = len(left_tokens & right_tokens) / max(len(left_tokens | right_tokens), 1)
    sequence = SequenceMatcher(None, left, right).ratio()
    return max(sequence, overlap)


def _normalize(value: str) -> str:
    text = value.lower()
    for token in (".", ",", "'", "\"", "-", "_"):
        text = text.replace(token, " ")

    stopwords = {"llc", "ltd", "inc", "co", "company", "the"}
    return " ".join(token for token in text.split() if token not in stopwords)
