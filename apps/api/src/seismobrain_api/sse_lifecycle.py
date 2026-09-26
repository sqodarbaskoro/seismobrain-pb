"""
File: sse_lifecycle.py
Description: SSE stream drain controller for graceful API shutdown (NFR-REL-07)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class SseStreamHandle:
    stream_id: str
    _controller: SseDrainController

    def close(self) -> None:
        self._controller.unregister(self.stream_id)


@dataclass
class SseDrainController:
    drain_seconds: int = 30
    _active: set[str] = field(default_factory=set)
    _draining: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def draining(self) -> bool:
        return self._draining

    @property
    def should_accept_new(self) -> bool:
        return not self._draining

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._active)

    def register(self, stream_id: str) -> SseStreamHandle:
        with self._lock:
            if self._draining:
                raise RuntimeError("refusing new SSE streams during drain")
            self._active.add(stream_id)
        return SseStreamHandle(stream_id=stream_id, _controller=self)

    def unregister(self, stream_id: str) -> None:
        with self._lock:
            self._active.discard(stream_id)

    def begin_shutdown(self) -> None:
        with self._lock:
            self._draining = True

    def wait_until_drained(self, *, timeout_s: float | None = None) -> bool:
        deadline = time.monotonic() + (
            self.drain_seconds if timeout_s is None else timeout_s
        )
        while time.monotonic() < deadline:
            if self.active_count == 0:
                return True
            time.sleep(0.01)
        return self.active_count == 0
