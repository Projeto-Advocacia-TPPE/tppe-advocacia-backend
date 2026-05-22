from app.modules.datajud.datajud_service import DataJudApiService
from app.modules.datajud.protocol import DataJudClient


def get_datajud_client() -> DataJudClient:
    return DataJudApiService()
