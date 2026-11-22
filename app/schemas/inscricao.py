from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

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
    presente: bool = False
    usuario_id: Optional[int] = None

    class Config:
        from_attributes = True
