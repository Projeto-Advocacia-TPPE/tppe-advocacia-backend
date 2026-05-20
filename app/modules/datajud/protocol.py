from typing import Protocol

from app.modules.datajud.schema import DataJudFetchResult


class DataJudClientError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class DataJudConfigurationError(DataJudClientError):
    pass


class DataJudProcessNotFoundInResponseError(DataJudClientError):
    pass


class DataJudClient(Protocol):
    def fetch_movements(
        self,
        process_number: str,
        tribunal_alias: str,
    ) -> DataJudFetchResult: ...
