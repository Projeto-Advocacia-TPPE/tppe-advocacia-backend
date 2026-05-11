from fastapi import status


class AppException(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidCredentialsError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Invalid credentials"
        )


class InactiveUserError(AppException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "INACTIVE_USER", "Inactive user")


class UnauthorizedError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Missing or invalid token"
        )


class ForbiddenError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Insufficient permissions"
        )


class UserNotFoundError(AppException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found")


class EmailAlreadyExistsError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT, "EMAIL_ALREADY_EXISTS", "Email already in use"
        )


class InvalidResetTokenError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_RESET_TOKEN",
            "Invalid or expired token",
        )


class ExpiredResetTokenError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_RESET_TOKEN",
            "Invalid or expired token",
        )
