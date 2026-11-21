from pydantic import BaseModel, EmailStr
from datetime import datetime

class InscricaoBase(BaseModel):
    nome_participante: str
    email_participante: EmailStr  
    evento_id: int

class InscricaoCreate(InscricaoBase):
    pass

class InscricaoResponse(InscricaoBase):
    id: int
    created_at: datetime
    status: str = "ATIVA"
    # [2AV] Presença registrada (necessária para emitir certificado - RN07).
    presente: bool = False

    class Config:
        from_attributes = True