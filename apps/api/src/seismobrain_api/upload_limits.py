"""
File: upload_limits.py
Description: Streamed upload byte limit — reject oversize before consuming remaining body
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

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator

DEFAULT_UPLOAD_MAX_BYTES = 200 * 1024 * 1024


class UploadTooLargeError(Exception):
    """Raised when an upload exceeds the configured size limit."""

    def __init__(self, *, max_bytes: int, bytes_read: int) -> None:
        self.max_bytes = max_bytes
        self.bytes_read = bytes_read
        super().__init__(
            f"upload exceeds limit of {max_bytes} bytes (read {bytes_read})"
        )


def read_limited_chunks(chunks: Iterator[bytes], *, max_bytes: int) -> bytes:
    """Read chunks until EOF or raise without consuming further chunks once over limit."""
    if max_bytes < 1:
        raise ValueError("max_bytes must be >= 1")
    parts: list[bytes] = []
    total = 0
    for chunk in chunks:
        total += len(chunk)
        if total > max_bytes:
            raise UploadTooLargeError(max_bytes=max_bytes, bytes_read=total)
        parts.append(chunk)
    return b"".join(parts)


ReadChunk = Callable[[int], Awaitable[bytes]]


async def read_upload_limited(
    read_chunk: ReadChunk,
    *,
    max_bytes: int,
    chunk_size: int = 64 * 1024,
) -> bytes:
    """Stream an upload via async read_chunk; stop reading once over max_bytes."""
    if max_bytes < 1:
        raise ValueError("max_bytes must be >= 1")

    async def _chunks() -> AsyncIterator[bytes]:
        while True:
            chunk = await read_chunk(chunk_size)
            if not chunk:
                return
            yield chunk

    parts: list[bytes] = []
    total = 0
    async for chunk in _chunks():
        total += len(chunk)
        if total > max_bytes:
            raise UploadTooLargeError(max_bytes=max_bytes, bytes_read=total)
        parts.append(chunk)
    return b"".join(parts)
