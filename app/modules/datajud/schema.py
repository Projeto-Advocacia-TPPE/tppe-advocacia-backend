from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.processes.schema import MovementRead
from app.shared.datajud import normalize_datajud_tribunal_alias


class DataJudMovement(BaseModel):
    external_id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    occurred_at: datetime


class DataJudFetchResult(BaseModel):
    movements: list[DataJudMovement]
    skipped_count: int = 0
    http_status: int | None = None


class DataJudSyncRequest(BaseModel):
    tribunal_alias: str | None = Field(default=None, min_length=2, max_length=30)

    @field_validator("tribunal_alias")
    @classmethod
    def normalize_alias(cls, value: str | None) -> str | None:
        return normalize_datajud_tribunal_alias(value)


class DataJudSyncResponse(BaseModel):
    process_id: int
    process_number: str
    tribunal_alias: str
    imported_count: int
    skipped_count: int
    external_api_log_id: int
    synced_at: datetime
    movements: list[MovementRead]


class DataJudBatchSyncRequest(BaseModel):
    tribunal_alias: str | None = Field(default=None, min_length=2, max_length=30)
    limit: int = Field(default=50, ge=1, le=100)

    @field_validator("tribunal_alias")
    @classmethod
    def normalize_alias(cls, value: str | None) -> str | None:
        return normalize_datajud_tribunal_alias(value)


class DataJudBatchSyncItem(BaseModel):
    process_id: int
    process_number: str
    tribunal_alias: str | None = None
    status: Literal["SUCCESS", "FAILURE"]
    imported_count: int = 0
    skipped_count: int = 0
    external_api_log_id: int | None = None
    error_code: str | None = None
    error_message: str | None = None


class DataJudBatchSyncResponse(BaseModel):
    tribunal_alias: str | None
    total_active_processes: int
    processed_count: int
    success_count: int
    failure_count: int
    imported_count: int
    skipped_count: int
    synced_at: datetime
    results: list[DataJudBatchSyncItem]
