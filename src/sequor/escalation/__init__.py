"""Sequor escalation engine — escalation creation, SLA tracking, and resolution."""

from sequor.escalation.scheduler import SLAScheduler, create_scheduler
from sequor.escalation.service import (
    BackupNotFoundError,
    EscalationError,
    EscalationNotFoundError,
    EscalationService,
)
from sequor.escalation.sla import calculate_deadline, is_breached, time_until_deadline
from sequor.escalation.thread_key import derive_thread_key, extract_topic

__all__ = [
    "BackupNotFoundError",
    "calculate_deadline",
    "create_scheduler",
    "derive_thread_key",
    "EscalationError",
    "EscalationNotFoundError",
    "EscalationService",
    "extract_topic",
    "is_breached",
    "SLAScheduler",
    "time_until_deadline",
]
