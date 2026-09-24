"""Custom exceptions for Mazda SDK."""


class MazdaError(Exception):
    """Base exception for all Mazda SDK errors."""
    pass


class MazdaAuthError(MazdaError):
    """Raised when authentication or token validation fails."""
    pass


class MazdaAPIError(MazdaError):
    """Raised when the API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None, code: str | int | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class MazdaConnectionError(MazdaError):
    """Raised when a network or connection error occurs."""
    pass


class MazdaRateLimitError(MazdaAPIError):
    """Raised when the API rate-limits the request."""


class MazdaCommandAuthError(MazdaAuthError):
    """Raised when remote-command signing material is rejected."""


class MazdaCommandNotReady(MazdaAuthError):
    """Raised when remote-command prerequisites are missing."""
