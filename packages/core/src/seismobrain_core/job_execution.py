"""Optional execution context provided by a worker to instrument real handler work."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from typing import Protocol


class Execution(Protocol):
    def stage(self, name: str) -> AbstractContextManager[dict[str, int]]: ...
    def publication(self) -> AbstractContextManager[None]: ...


current_execution: ContextVar[Execution | None] = ContextVar("job_execution", default=None)


@contextmanager
def ingestion_stage(name: str) -> Iterator[dict[str, int]]:
    execution = current_execution.get()
    if execution is None:
        yield {}
    else:
        with execution.stage(name) as counts:
            yield counts


@contextmanager
def ingestion_publication() -> Iterator[None]:
    execution = current_execution.get()
    if execution is None:
        yield
    else:
        with execution.publication():
            yield
