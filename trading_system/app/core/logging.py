import logging
import sys

from pythonjsonlogger.json import JsonFormatter


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "service"):
            record.service = "trading-system"
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(service)s %(message)s %(filename)s %(lineno)d"
        )
    )
    handler.addFilter(ContextFilter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
