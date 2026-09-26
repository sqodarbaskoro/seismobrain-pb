"""
File: folder_ingestion.py
Description: Allowlisted folder ingestion with globs, dry-run, stop/resume (FR-DOC-06)
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

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path


class FolderIngestionError(ValueError):
    """Raised when a folder job violates allowlist or symlink containment."""


@dataclass(slots=True)
class ListedFile:
    path: Path
    metadata: dict[str, object]


@dataclass
class FolderIngestionJob:
    collection_id: str
    root: Path
    include: list[str]
    exclude: list[str]
    dry_run: bool = False
    force_reindex: bool = False
    cursor: str | None = None
    indexed: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FolderIngestionResult:
    status: str
    dry_run: bool
    files: list[ListedFile] = field(default_factory=list)
    indexed: list[str] = field(default_factory=list)
    reindexed: int = 0


class FolderIngestionRunner:
    """Scans allowlisted roots with path containment and resumable indexing."""

    def __init__(self, *, allowlisted_roots: list[Path]) -> None:
        if not allowlisted_roots:
            raise ValueError("allowlisted_roots must not be empty")
        self._roots = [root.resolve() for root in allowlisted_roots]
        self._indexed: set[tuple[str, str]] = set()

    def run(
        self,
        job: FolderIngestionJob,
        *,
        stop_after: int | None = None,
    ) -> FolderIngestionResult:
        root = self._require_allowlisted_root(job.root)
        matches = self._list_matches(job, root)
        if job.dry_run:
            files = [
                ListedFile(
                    path=path,
                    metadata={
                        "size_bytes": path.stat().st_size,
                        "relative_path": path.relative_to(root).as_posix(),
                    },
                )
                for path in matches
            ]
            return FolderIngestionResult(status="completed", dry_run=True, files=files)

        start_index = 0
        if job.cursor is not None:
            for index, path in enumerate(matches):
                if path.relative_to(root).as_posix() == job.cursor:
                    start_index = index + 1
                    break

        newly_indexed: list[str] = []
        reindexed = 0
        for path in matches[start_index:]:
            relative = path.relative_to(root).as_posix()
            key = (job.collection_id, relative)
            already = key in self._indexed
            if already and not job.force_reindex:
                job.cursor = relative
                continue
            self._indexed.add(key)
            newly_indexed.append(relative)
            job.indexed.append(relative)
            if already and job.force_reindex:
                reindexed += 1
            job.cursor = relative
            if stop_after is not None and len(newly_indexed) >= stop_after:
                return FolderIngestionResult(
                    status="stopped",
                    dry_run=False,
                    indexed=list(job.indexed),
                    reindexed=reindexed,
                )

        return FolderIngestionResult(
            status="completed",
            dry_run=False,
            indexed=list(job.indexed),
            reindexed=reindexed,
        )

    def resume(self, job: FolderIngestionJob) -> FolderIngestionResult:
        return self.run(job)

    def _require_allowlisted_root(self, root: Path) -> Path:
        resolved = root.resolve()
        for allowed in self._roots:
            try:
                resolved.relative_to(allowed)
                return resolved
            except ValueError:
                continue
        raise FolderIngestionError(f"root is not under an allowlisted path: {root}")

    def _list_matches(self, job: FolderIngestionJob, root: Path) -> list[Path]:
        matches: list[Path] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() and not path.is_symlink():
                continue
            self._assert_contained(path, root)
            relative = path.relative_to(root).as_posix()
            if job.include and not any(
                fnmatch.fnmatch(relative, pattern) for pattern in job.include
            ):
                continue
            if any(fnmatch.fnmatch(relative, pattern) for pattern in job.exclude):
                continue
            if path.is_symlink() or path.is_file():
                matches.append(path)
        return matches

    def _assert_contained(self, path: Path, root: Path) -> None:
        if path.is_symlink():
            target = path.resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise FolderIngestionError(
                    f"symlink escapes allowlisted root: {path}"
                ) from exc
            return
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise FolderIngestionError(
                f"path escapes allowlisted root: {path}"
            ) from exc
