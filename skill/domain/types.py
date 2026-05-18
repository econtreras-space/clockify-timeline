from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ConstraintType(str, Enum):
    FIXED_MEETING = "fixed_meeting"
    LUNCH_BREAK = "lunch_break"
    WORKDAY_BOUNDARY = "workday_boundary"
    CALENDAR_ANCHOR = "calendar_anchor"


class WorkCategory(str, Enum):
    DEVELOPMENT = "development"
    REVIEW = "review"
    MEETING = "meeting"
    PLANNING = "planning"
    OPERATIONS = "operations"
    COMMUNICATION = "communication"
    OTHER = "other"


class ValidationOutcome(str, Enum):
    PASS = "pass"
    WARN = "warn"
    NEEDS_CLARIFICATION = "needs_clarification"
    REJECT = "reject"


# ---------------------------------------------------------------------------
# Core domain entities
# ---------------------------------------------------------------------------

@dataclass
class NarrativeInput:
    """Raw human update plus the minimal context needed to interpret it."""
    raw_text: str
    report_date: date
    timezone: str = "America/Montevideo"
    source_context: Optional[str] = None  # e.g. "slack-eod", "manual"


@dataclass
class WorkUnit:
    """Semantic unit of work extracted from narrative — no time assigned yet."""
    description: str
    category: WorkCategory = WorkCategory.OTHER
    relative_weight: float = 1.0            # semantic importance, not hours
    ambiguity_markers: list[str] = field(default_factory=list)


@dataclass
class Constraint:
    """Hard temporal boundary or reserved time anchor."""
    constraint_type: ConstraintType
    start: datetime
    end: datetime
    label: str
    origin: str = "schedule_config"         # "schedule_config" | "calendar" | "user"
    is_hard: bool = True                    # hard = must not be allocated over


@dataclass
class AvailableGap:
    """Allocatable time surface remaining after all constraints are applied."""
    start: datetime
    end: datetime

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    @property
    def hours(self) -> float:
        return self.duration.total_seconds() / 3600


@dataclass
class TimelineBlock:
    """A single reconstructed temporal block — output of the Analyzer."""
    start: datetime
    end: datetime
    description: str
    work_unit_ref: Optional[WorkUnit] = None
    confidence: float = 1.0                 # 0.0–1.0; affects ValidationState
    trace: str = ""                         # human-readable reasoning note

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    @property
    def hours(self) -> float:
        return self.duration.total_seconds() / 3600


@dataclass
class ValidationState:
    """Explicit confidence and ambiguity signals attached to a TimelineProposal."""
    outcome: ValidationOutcome
    warnings: list[str] = field(default_factory=list)
    clarification_questions: list[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None

    @property
    def needs_clarification(self) -> bool:
        return self.outcome == ValidationOutcome.NEEDS_CLARIFICATION

    @property
    def is_blocked(self) -> bool:
        return self.outcome in (ValidationOutcome.NEEDS_CLARIFICATION, ValidationOutcome.REJECT)


@dataclass
class TimelineProposal:
    """Full-day proposal ready for human review — not yet provider-translated."""
    report_date: date
    blocks: list[TimelineBlock] = field(default_factory=list)
    validation: Optional[ValidationState] = None
    narrative_source: Optional[NarrativeInput] = None

    @property
    def total_hours(self) -> float:
        return sum(b.hours for b in self.blocks)

    @property
    def is_confirmed(self) -> bool:
        return (
            self.validation is not None
            and self.validation.outcome == ValidationOutcome.PASS
        )


@dataclass
class ClockifyEntry:
    """Provider-specific shape for a single Clockify time entry."""
    date: str           # "YYYY-MM-DD"
    start: str          # "HH:MM"
    end: str            # "HH:MM"
    description: str
    hours: float


@dataclass
class ProviderPayload:
    """Provider-facing output derived from an accepted TimelineProposal."""
    provider: str                               # e.g. "clockify"
    entries: list[ClockifyEntry] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    submission_ready: bool = False
