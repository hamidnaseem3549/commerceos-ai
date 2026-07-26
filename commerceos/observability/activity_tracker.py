"""Records every agent action -> AgentLog table."""
from commerceos.database.connection import get_session
from commerceos.database.models import AgentLog
from commerceos.observability.logger import get_logger

_logger = get_logger("activity_tracker")


def track(agent_name: str, action: str, detail: str = "",
          level: str = "INFO", query_id: str | None = None) -> None:
    _logger.info(f"[{agent_name}] {action}: {detail[:200]}",
                 extra={"agent": agent_name, "action": action})
    try:
        session = get_session()
        session.add(AgentLog(agent_name=agent_name, action=action,
                             detail=detail[:500], level=level, query_id=query_id))
        session.commit()
        session.close()
    except Exception as e:  # noqa: BLE001
        _logger.warning(f"Failed to persist agent log: {e}")
