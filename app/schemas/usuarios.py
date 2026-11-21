from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    # [2AV] Senha com no mínimo 6 caracteres.
    senha: str = Field(min_length=6)

    # [2AV] O bcrypt só aceita até 72 bytes; acima disso devolvemos 422 em vez de erro 500.
    @field_validator("senha")
    @classmethod
    def validar_tamanho_senha(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("A senha deve ter no máximo 72 bytes.")
        return v

class UsuarioResponse(BaseModel):
    # [2AV] Resposta de usuário: nunca inclui senha nem senha_hash.
    id: int
    # [2AV] Optional porque a coluna nome aceita nulo no Supabase (evita 500 ao listar).
    nome: Optional[str] = None
    email: str
    # [2AV] Campo para o CRUD de usuários (RF03): indica se o usuário está ativo.
    ativo: bool = True

    class Config:
        from_attributes = True

# [2AV] Dados que podem ser editados no PUT /usuarios/{id} (RF03).
class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None

# [2AV] O LoginRequest (JSON) foi removido: o login agora usa o formulário OAuth2,
# que é o formato enviado pelo botão "Authorize" do Swagger.

class Token(BaseModel):
    access_token: str
    token_type: str
