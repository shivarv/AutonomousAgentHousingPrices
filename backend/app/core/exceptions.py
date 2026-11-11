"""Domain exceptions raised by services; main.py maps them to HTTP status codes."""


class DomainError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class ValidationError(DomainError):
    status_code = 422


class OutsideCoverageError(DomainError):
    """A point or filter lies outside Massachusetts (or outside the requested layer)."""

    status_code = 422
