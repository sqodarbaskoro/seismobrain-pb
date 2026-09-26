"""
File: lockout.py
Description: Account lockout with progressive delay after failed logins (FR-AUTH-08)
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

import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class AccountLockout:
    """Tracks failed logins and applies progressive delays per account."""

    clock: Callable[[], float] = time.time
    failure_threshold: int = 3
    max_delay_seconds: int = 300
    _failures: dict[str, int] = field(default_factory=dict)
    _locked_until: dict[str, float] = field(default_factory=dict)

    def remaining_delay(self, account: str) -> float:
        until = self._locked_until.get(account.lower(), 0.0)
        remaining = until - self.clock()
        return remaining if remaining > 0 else 0.0

    def record_failure(self, account: str) -> float:
        key = account.lower()
        count = self._failures.get(key, 0) + 1
        self._failures[key] = count
        if count <= self.failure_threshold:
            return 0.0
        # Progressive: 1, 2, 4, ... seconds after the threshold is exceeded.
        exponent = count - self.failure_threshold - 1
        delay = min(2**exponent, self.max_delay_seconds)
        self._locked_until[key] = self.clock() + delay
        return float(delay)

    def record_success(self, account: str) -> None:
        key = account.lower()
        self._failures.pop(key, None)
        self._locked_until.pop(key, None)
