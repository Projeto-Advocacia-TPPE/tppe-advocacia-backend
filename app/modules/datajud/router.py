from fastapi import APIRouter, Body, Depends

from app.modules.datajud.deps import get_datajud_service
from app.modules.datajud.schema import (
    DataJudBatchSyncRequest,
    DataJudBatchSyncResponse,
    DataJudSyncRequest,
    DataJudSyncResponse,
)
from app.modules.datajud.service import DataJudService
from app.modules.users.model import User
from app.shared.deps.auth import get_current_user, require_admin
from app.shared.http.responses import SuccessResponse, error_responses, ok

router = APIRouter(tags=["DataJud"])


@router.post(
    "/processes/{process_id}/sync",
    response_model=SuccessResponse[DataJudSyncResponse],
    responses=error_responses(401, 404, 422, 502, 503),
    summary="Sincroniza movimentações processuais pela API pública do DataJud",
)
def sync_process_movements_from_datajud(
    process_id: int,
    payload: DataJudSyncRequest | None = Body(default=None),
    service: DataJudService = Depends(get_datajud_service),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[DataJudSyncResponse]:
    return ok(
        service.sync_process_movements(
            process_id=process_id,
            payload=payload or DataJudSyncRequest(),
            actor_id=current_user.id,
        )
    )


@router.post(
    "/datajud/sync-active-processes",
    response_model=SuccessResponse[DataJudBatchSyncResponse],
    responses=error_responses(401, 403, 422, 502, 503),
    summary="Sincroniza movimentações DataJud dos processos ativos",
)
def sync_active_processes_from_datajud(
    payload: DataJudBatchSyncRequest,
    service: DataJudService = Depends(get_datajud_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse[DataJudBatchSyncResponse]:
    return ok(
        service.sync_active_processes(
            payload=payload,
            actor_id=current_user.id,
        )
    )
