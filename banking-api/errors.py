# errors.py
# Shared domain exceptions used across the service layer.
# Controllers translate these into HTTP responses (404, 400, etc.).


class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""


class ValidationError(Exception):
    """Raised when input fails a business rule (e.g. duplicate email)."""


class AuthError(Exception):
    """Raised when login fails or a request has no valid login token (-> 401)."""


class ForbiddenError(Exception):
    """Raised when you ARE logged in but not allowed to do this (-> 403)."""


class RateLimitError(Exception):
    """Raised after too many wrong passwords (-> 429 Too Many Requests)."""
