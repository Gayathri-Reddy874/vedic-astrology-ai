"""Domain-level exceptions."""


class ValidationError(ValueError):
    """Raised when user-supplied birth data or request payloads are invalid."""
