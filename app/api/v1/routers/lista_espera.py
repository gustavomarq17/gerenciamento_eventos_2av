from fastapi import APIRouter, HTTPException, status
from app.schemas.lista_espera import ListaEsperaCreate, ListaEsperaResponse
from app.database.connection import supabase

router = APIRouter(prefix="/lista-espera", tags=["Lista de Espera"])

@router.post("/", response_model=ListaEsperaResponse, status_code=status.HTTP_201_CREATED)
def entrar_lista_espera(dados: ListaEsperaCreate):
    # 1. Verifica se o evento existe
    evento_resp = supabase.table("eventos").select("*").eq("id", dados.evento_id).execute()
    if not evento_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
    
    # 2. Verifica se já está na lista de espera
    existente = supabase.table("lista_espera") \
        .select("*") \
        .eq("evento_id", dados.evento_id) \
        .eq("email_participante", dados.email_participante) \
        .execute()
    
    if existente.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Você já está na lista de espera deste evento.")

    # 3. Insere na fila
    payload = dados.model_dump()
    response = supabase.table("lista_espera").insert(payload).execute()

    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao entrar na lista de espera.")

    return response.data[0]