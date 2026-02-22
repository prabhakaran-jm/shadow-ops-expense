"""Optional post-run notifier. Log-only implementation; can be extended to email/Slack etc."""

from app.logging_config import get_logger

logger = get_logger(__name__)


def notify_run_completed(session_id: str, confirmation_id: str | None, run_id: str) -> None:
    """
    Notify that an agent run completed (e.g. expense submitted).
    Currently logs only; can be extended to send to manager email, Slack, etc.
    """
    logger.info(
        "would_notify_manager",
        message="Expense submitted",
        session_id=session_id,
        confirmation_id=confirmation_id,
        run_id=run_id,
    )
