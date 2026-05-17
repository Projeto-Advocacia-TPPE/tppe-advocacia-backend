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


class FileTooLargeError(AppException):
    def __init__(self, max_mb: int) -> None:
        super().__init__(
            status.HTTP_413_CONTENT_TOO_LARGE,
            "FILE_TOO_LARGE",
            f"File exceeds maximum allowed size of {max_mb}MB",
        )


class InvalidMimeTypeError(AppException):
    def __init__(self, allowed: list[str]) -> None:
        super().__init__(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "INVALID_MIME_TYPE",
            f"File type not allowed. Accepted: {', '.join(allowed)}",
        )


class MediaNotFoundError(AppException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "MEDIA_NOT_FOUND", "File not found")


class ArticleNotFoundError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_404_NOT_FOUND, "ARTICLE_NOT_FOUND", "Article not found"
        )


class LeadNotFoundError(AppException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "LEAD_NOT_FOUND", "Lead not found")


class LeadDuplicateError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "LEAD_DUPLICATE",
            "A lead with this email was already submitted recently",
        )


class AssigneeNotFoundError(AppException):
    def __init__(self) -> None:
        super().__init__(422, "ASSIGNEE_NOT_FOUND", "Assigned user does not exist")


class ClientNotFoundError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_404_NOT_FOUND, "CLIENT_NOT_FOUND", "Client not found"
        )


class ClientCpfAlreadyExistsError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "CLIENT_CPF_ALREADY_EXISTS",
            "A client with this CPF already exists",
        )


class ClientCnpjAlreadyExistsError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "CLIENT_CNPJ_ALREADY_EXISTS",
            "A client with this CNPJ already exists",
        )


class ClientNoteNotFoundError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "CLIENT_NOTE_NOT_FOUND",
            "Client note not found",
        )


class ProcessNotFoundError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_404_NOT_FOUND, "PROCESS_NOT_FOUND", "Process not found"
        )


class ProcessNumberAlreadyExistsError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "PROCESS_NUMBER_ALREADY_EXISTS",
            "A process with this number already exists",
        )


class ClientNotFoundForProcessError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "CLIENT_NOT_FOUND_FOR_PROCESS",
            "Referenced client does not exist",
        )


class ProcessStatusUnchangedError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "PROCESS_STATUS_UNCHANGED",
            "Process is already in the requested status",
        )
