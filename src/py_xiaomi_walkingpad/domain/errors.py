class WalkingPadAppError(Exception):
    """Base error for the application."""


class ConfigurationError(WalkingPadAppError):
    """Raised when required configuration is missing or invalid."""


class DeviceCommunicationError(WalkingPadAppError):
    """Raised when communication with the pad fails."""


class CommandValidationError(WalkingPadAppError):
    """Raised when command arguments are invalid."""

