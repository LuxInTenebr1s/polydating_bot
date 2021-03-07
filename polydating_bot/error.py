"""Module to describe custom errors."""

class PolydatingError(BaseException):
    """Polydating base exception."""

class MissingDataError(Exception):
    """Error on missing data."""

class IncorrectIdError(Exception):
    """Error on unknown ID."""

class PersistenceError(Exception):
    """Something wrong with persistence."""

class AnswerError(Exception):
    """Incorrect answer."""

class CommandError(Exception):
    """Incorrect command."""

class NoMediaError(PolydatingError):
    """No media found."""
