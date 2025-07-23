# src/utils/exceptions.py

class RealEstatePlatformException(Exception):
    """Base exception class for the application.
    
    Allows us to catch all our custom exceptions with a single 'except' block.
    """
    def __init__(self, message="An application-specific error occurred."):
        self.message = message
        super().__init__(self.message)

class DatabaseError(RealEstatePlatformException):
    """Raised for general database-related errors."""
    def __init__(self, message="A database error occurred. Please try again later."):
        super().__init__(message)

class NotFoundError(RealEstatePlatformException):
    """Base class for not-found errors."""
    pass

class UserNotFoundError(NotFoundError):
    """Raised when a specific user cannot be found in the database."""
    def __init__(self, identifier: str | int):
        message = f"Could not find user: {identifier}."
        super().__init__(message)

class PropertyNotFoundError(NotFoundError):
    """Raised when a specific property cannot be found in the database."""
    def __init__(self, identifier: str):
        message = f"Could not find property: {identifier}."
        super().__init__(message)

class InvalidOperationError(RealEstatePlatformException):
    """Raised when a user attempts an action that is not permitted by business logic."""
    def __init__(self, message="This operation is not permitted."):
        super().__init__(message)

class TelegramApiError(RealEstatePlatformException):
    """Raised when a call to the Telegram API fails."""
    def __init__(self, message="There was a problem communicating with Telegram. Please try again."):
        super().__init__(message)