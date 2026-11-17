from pydantic import BaseModel, EmailStr

class ListaEsperaCreate(BaseModel):
    participante_id: int
    evento_id: int
    nome_participante: str
    email_participante: EmailStr

class ListaEsperaResponse(ListaEsperaCreate):
    id: int

    class Config:
        from_attributes = True