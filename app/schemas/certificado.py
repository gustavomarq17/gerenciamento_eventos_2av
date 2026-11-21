# [2AV] Schemas dos certificados (RF10/RF11): dados para emitir e dados devolvidos pela API.
from pydantic import BaseModel
from datetime import datetime

class CertificadoCreate(BaseModel):
    inscricao_id: int

class CertificadoResponse(BaseModel):
    id: int
    created_at: datetime
    inscricao_id: int
    codigo_validador: str

    class Config:
        from_attributes = True
