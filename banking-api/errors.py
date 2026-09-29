# errors.py
# Shared domain exceptions used across the service layer.
# Controllers translate these into HTTP responses (404, 400, etc.).


class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""


class ValidationError(Exception):
    """Raised when input fails a business rule (e.g. duplicate email)."""
