import sys
import structlog
from structlog.types import EventDict, Processor
from app.core.config import settings


def add_log_level(
    logger: structlog.BoundLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    event_dict["level"] = method_name.upper()
    return event_dict


def add_timestamp(
    logger: structlog.BoundLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    import datetime

    event_dict["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    return event_dict


def filter_secrets(
    logger: structlog.BoundLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    sensitive_keys = {"password", "secret", "key", "token", "api_key"}
    for key in list(event_dict.keys()):
        if any(s in key.lower() for s in sensitive_keys):
            event_dict[key] = "***REDACTED***"
    return event_dict


def setup_logging() -> None:
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_timestamp,
        filter_secrets,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]

    if settings.is_development:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    import logging

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.app_log_level.upper()),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
