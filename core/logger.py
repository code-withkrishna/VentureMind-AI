from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from core.config import Settings
from core.models import TraceEvent


def configure_logging(settings: Settings) -> logging.Logger:
    logger = logging.getLogger("agentathon")
    if logger.handlers:
        return logger

    settings.ensure_directories()

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(settings.logs_dir / "agentathon.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


class TraceRecorder:
    def __init__(
        self,
        settings: Settings,
        run_id: str,
        logger: logging.Logger,
        callback: Callable[[TraceEvent], None] | None = None,
    ) -> None:
        self.settings = settings
        self.run_id = run_id
        self.logger = logger
        self.callback = callback
        self.events: list[TraceEvent] = []

    @property
    def output_path(self) -> Path:
        return self.settings.trace_dir / f"{self.run_id}.json"

    def record(
        self,
        stage: str,
        title: str,
        details: str,
        metadata: dict | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            stage=stage,
            title=title,
            details=details,
            metadata=metadata or {},
        )
        self.events.append(event)
        self.logger.info("%s | %s | %s", stage.upper(), title, details)
        if self.callback is not None:
            self.callback(event)
        return event

    def save(self) -> str:
        self.settings.trace_dir.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w", encoding="utf-8") as handle:
            json.dump([asdict(event) for event in self.events], handle, indent=2)
        return str(self.output_path)
