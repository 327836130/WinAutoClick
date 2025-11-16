from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LogRecord:
    level: str
    message: str
    task_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)


class LogStore:
    def __init__(self, max_records: int = 500) -> None:
        self._max = max_records
        self._records: List[LogRecord] = []
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._records = []

    def append(self, record: LogRecord) -> None:
        with self._lock:
            self._records.append(record)
            # Keep memory bounded.
            if len(self._records) > self._max:
                self._records = self._records[-self._max :]

    def log(self, message: str, level: str = "INFO", task_id: Optional[str] = None) -> None:
        self.append(LogRecord(level=level, message=message, task_id=task_id))

    def list_recent(self, limit: int = 200) -> List[LogRecord]:
        with self._lock:
            if limit <= 0:
                return list(self._records)
            return list(self._records[-limit:])


log_store = LogStore()
