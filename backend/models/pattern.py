from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


PatternType = Literal["bulk_filing_day", "repeat_plaintiff", "zip_cluster"]
PatternSeverity = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class PatternSignal:
    type: PatternType
    severity: PatternSeverity
    description: str
    anomaly_score: float
    matching_cases: int = 0

    def model_dump(self) -> dict:
        return asdict(self)
