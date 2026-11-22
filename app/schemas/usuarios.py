from typing import Optional
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str = Field(min_length=6)

    @field_validator("senha")
    @classmethod
    def validar_tamanho_senha(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("A senha deve ter no máximo 72 bytes.")
        return v

class UsuarioResponse(BaseModel):
    id: int
    nome: Optional[str] = None
    email: str
    ativo: bool = True
    perfil: Optional[str] = None

    class Config:
        from_attributes = True

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None

class PerfilUpdate(BaseModel):
    perfil: Literal["ADMIN", "ORGANIZADOR", "PARTICIPANTE"]


class Token(BaseModel):
    access_token: str
    token_type: str
    perfil: Optional[str] = None
