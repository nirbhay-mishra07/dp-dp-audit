"""Shared finding schema used by all auditor modules."""

from dataclasses import asdict, dataclass
from typing import Any, Literal

Status = Literal["pass", "fail", "warning", "manual_review", "not_applicable", "not_yet_effective"]
Severity = Literal["critical", "high", "medium", "low", "informational"]
Confidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class Finding:
    control_id: str
    status: Status
    severity: Severity
    title: str
    description: str
    file: str
    line: int
    evidence: str
    recommendation: str
    confidence: Confidence
    legal_reference: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
