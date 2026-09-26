"""
File: test_folder_ingestion.py
Description: FR-DOC-06 / SEC-16 — folder ingestion roots, globs, dry-run, stop/resume
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

from pathlib import Path

import pytest

from seismobrain_ingest.folder_ingestion import (
    FolderIngestionError,
    FolderIngestionJob,
    FolderIngestionRunner,
)


@pytest.fixture
def scan_tree(tmp_path: Path) -> Path:
    root = tmp_path / "scan"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "a.txt").write_text("a", encoding="utf-8")
    (root / "docs" / "b.md").write_text("# b", encoding="utf-8")
    (root / "docs" / "skip.tmp").write_text("x", encoding="utf-8")
    (root / "other").mkdir()
    (root / "other" / "c.txt").write_text("c", encoding="utf-8")
    return root


def test_dry_run_lists_files_with_globs(scan_tree: Path) -> None:
    runner = FolderIngestionRunner(allowlisted_roots=[scan_tree])
    job = FolderIngestionJob(
        collection_id="col-1",
        root=scan_tree,
        include=["**/*.txt", "**/*.md"],
        exclude=["**/*.tmp"],
        dry_run=True,
    )
    result = runner.run(job)
    assert result.status == "completed"
    assert result.dry_run is True
    paths = [item.path.name for item in result.files]
    assert sorted(paths) == ["a.txt", "b.md", "c.txt"]
    assert all(item.metadata["size_bytes"] > 0 for item in result.files)


def test_rejects_path_outside_allowlist_and_external_symlink(
    scan_tree: Path, tmp_path: Path
) -> None:
    runner = FolderIngestionRunner(allowlisted_roots=[scan_tree])
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "leak.txt").write_text("secret", encoding="utf-8")

    with pytest.raises(FolderIngestionError, match="allowlisted"):
        runner.run(
            FolderIngestionJob(
                collection_id="col-1",
                root=outside,
                include=["**/*"],
                exclude=[],
                dry_run=True,
            )
        )

    link = scan_tree / "docs" / "escape.txt"
    link.symlink_to(outside / "leak.txt")
    with pytest.raises(FolderIngestionError, match="symlink"):
        runner.run(
            FolderIngestionJob(
                collection_id="col-1",
                root=scan_tree,
                include=["**/escape.txt"],
                exclude=[],
                dry_run=True,
            )
        )


def test_stop_resume_and_force_reindex(scan_tree: Path) -> None:
    runner = FolderIngestionRunner(allowlisted_roots=[scan_tree])
    job = FolderIngestionJob(
        collection_id="col-1",
        root=scan_tree,
        include=["**/*.txt"],
        exclude=[],
        dry_run=False,
    )
    # Process one file then stop.
    partial = runner.run(job, stop_after=1)
    assert partial.status == "stopped"
    assert len(partial.indexed) == 1
    assert job.cursor is not None

    resumed = runner.resume(job)
    assert resumed.status == "completed"
    assert len(resumed.indexed) == 2  # a.txt + c.txt total across runs via cursor

    # Force re-index reprocesses known files.
    forced = runner.run(
        FolderIngestionJob(
            collection_id="col-1",
            root=scan_tree,
            include=["**/*.txt"],
            exclude=[],
            dry_run=False,
            force_reindex=True,
        )
    )
    assert forced.status == "completed"
    assert len(forced.indexed) == 2
    assert forced.reindexed == 2
