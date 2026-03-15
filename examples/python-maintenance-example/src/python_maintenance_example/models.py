from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["critical", "high", "medium", "low"]


class DependencyFinding(BaseModel):
    package: str
    severity: Severity
    current_version: str
    fixed_versions: list[str] = Field(default_factory=list)
    advisory_id: str
    summary: str


class AuditEnvelope(BaseModel):
    project_name: str
    findings: list[DependencyFinding]
