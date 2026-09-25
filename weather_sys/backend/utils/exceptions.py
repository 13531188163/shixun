"""Application exceptions that are safe to expose through the API."""

from __future__ import annotations

from typing import Any, Optional


class AppException(Exception):
    """Base exception with a client-safe message and HTTP status."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        data: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data


class DatabaseUnavailableError(AppException):
    """Raised when MySQL cannot be connected to or does not answer."""

    def __init__(self, message: str = "database unavailable") -> None:
        super().__init__(message=message, status_code=503)
