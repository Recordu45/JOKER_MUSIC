"""
Custom exceptions used across the JOKER_MUSIC project.
These exceptions carry extra context (attributes) to make
error handling and logging easier.
"""

from typing import Optional


class BotError(Exception):
    """Base class for bot-specific exceptions."""
    def __init__(self, message: Optional[str] = None):
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__

    def __str__(self) -> str:
        return self.message


class DurationLimitError(BotError):
    """
    Raised when a media duration exceeds allowed limits.

    Attributes:
        duration: int | float - duration in seconds that triggered the error
        limit: int | float | None - configured limit in seconds (if known)
    """
    def __init__(self, duration: float, limit: Optional[float] = None, message: Optional[str] = None):
        msg = message or f"Duration {duration}s exceeds limit {limit}s" if limit is not None else f"Duration {duration}s not allowed"
        super().__init__(msg)
        self.duration = duration
        self.limit = limit


class FFmpegReturnCodeError(BotError):
    """
    Raised when an FFmpeg process returns a non-zero code.

    Attributes:
        returncode: int - the FFmpeg return code
        cmd: Optional[str] - the ffmpeg command that was run
        stderr: Optional[str] - stderr output (if captured)
    """
    def __init__(self, returncode: int, cmd: Optional[str] = None, stderr: Optional[str] = None, message: Optional[str] = None):
        msg = message or f"FFmpeg exited with code {returncode}"
        super().__init__(msg)
        self.returncode = returncode
        self.cmd = cmd
        self.stderr = stderr

    def __str__(self) -> str:
        base = super().__str__()
        if self.cmd:
            base += f"\nCommand: {self.cmd}"
        if self.stderr:
            # keep stderr short to avoid huge logs, but include useful part
            snippet = (self.stderr[:1000] + "...") if len(self.stderr) > 1000 else self.stderr
            base += f"\nStderr: {snippet}"
        return base


__all__ = ["BotError", "DurationLimitError", "FFmpegReturnCodeError"]
