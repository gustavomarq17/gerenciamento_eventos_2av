from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.inscricao import InscricaoCreate, InscricaoResponse
from app.utils.security import obter_usuario_atual
from app.database.connection import supabase

router = APIRouter(prefix="/inscricoes", tags=["Inscrições"])

@router.get("/", response_model=list[InscricaoResponse])
def listar_inscricoes():
    """Listar todas as inscrições efetuadas."""
    response = supabase.table("inscricoes").select("*").execute()
    return response.data

# [2AV] Havia dois POST "/" neste arquivo. Na execução valia o primeiro (sem as regras de negócio)
# e o Swagger mostrava o segundo (sem cadeado). O duplicado foi removido e esta rota, que tem as
# regras RN02/RN03/RN08, passou a exigir token JWT (rota protegida).
@router.post("/", response_model=InscricaoResponse, status_code=status.HTTP_201_CREATED)
def realizar_inscricao(inscricao: InscricaoCreate, usuario_atual: dict = Depends(obter_usuario_atual)):
    """Realizar inscrição em um evento (RF07)."""

    evento_resp = supabase.table("eventos").select("*").eq("id", inscricao.evento_id).execute()
    if not evento_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento informado não existe.")
    
    evento = evento_resp.data[0]

    if evento.get("status") != "ATIVO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não é possível se inscrever em eventos inativos ou cancelados.")

    inscricao_existente = supabase.table("inscricoes") \
        .select("*") \
        .eq("evento_id", inscricao.evento_id) \
        .eq("email_participante", inscricao.email_participante) \
        .execute()
    
    if inscricao_existente.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este participante já está inscrito neste evento.")

    inscritos_atuais = supabase.table("inscricoes") \
        .select("id", count="exact") \
        .eq("evento_id", inscricao.evento_id) \
        .execute()
    
    total_inscritos = inscritos_atuais.count if inscritos_atuais.count is not None else len(inscritos_atuais.data)
    capacidade_maxima = evento.get("capacidade", 50)

    if total_inscritos >= capacidade_maxima:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Capacidade máxima do evento já foi atingida.")

    dados = inscricao.model_dump()
    dados["status"] = "ATIVA"
    
    response = supabase.table("inscricoes").insert(dados).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao realizar inscrição.")
    
    return response.data[0]

# [2AV] Marca a presença do participante na inscrição (necessária para emitir certificado - RN07).
@router.patch("/{inscricao_id}/presenca", response_model=InscricaoResponse)
def marcar_presenca(inscricao_id: int, usuario_atual: dict = Depends(obter_usuario_atual)):
    """Registra a presença do participante em uma inscrição."""
    response = supabase.table("inscricoes").update({"presente": True}).eq("id", inscricao_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada.")
    return response.data[0]

@router.delete("/{inscricao_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_inscricao(inscricao_id: int):
    """Cancela inscrição e promove automaticamente o primeiro da fila de espera."""
    
    inscricao_resp = supabase.table("inscricoes").select("*").eq("id", inscricao_id).execute()
    if not inscricao_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada.")
    
    inscricao = inscricao_resp.data[0]
    evento_id = inscricao["evento_id"]

    delete_resp = supabase.table("inscricoes").delete().eq("id", inscricao_id).execute()
    if not delete_resp.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao cancelar inscrição.")

    fila_resp = supabase.table("lista_espera") \
        .select("*") \
        .eq("evento_id", evento_id) \
        .order("data_criacao", desc=False) \
        .limit(1) \
        .execute()

    if fila_resp.data:
        proximo = fila_resp.data[0]
        
        nova_inscricao = {
            "evento_id": proximo["evento_id"],
            "nome_participante": proximo["nome_participante"],
            "email_participante": proximo["email_participante"]
        }
        
        supabase.table("inscricoes").insert(nova_inscricao).execute()
        
        supabase.table("lista_espera").delete().eq("id", proximo["id"]).execute()

    return None