from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.evento import EventoCreate, EventoResponse, EventoUpdate
from app.utils.security import obter_usuario_atual, exigir_perfil
from app.database.connection import supabase

router = APIRouter(prefix="/eventos", tags=["Eventos"])

@router.get("/", response_model=list[EventoResponse])
def listar_eventos(usuario_atual: dict = Depends(obter_usuario_atual)):
    """Listar todos os eventos cadastrados (RF05)."""
    response = supabase.table("eventos").select("*").execute()
    return response.data

@router.get("/{evento_id}", response_model=EventoResponse)
def obter_evento(evento_id: int, usuario_atual: dict = Depends(obter_usuario_atual)):
    """Obter detalhes de um evento pelo ID."""
    response = supabase.table("eventos").select("*").eq("id", evento_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
    return response.data[0]

@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_evento(dados: EventoCreate, usuario_atual: dict = Depends(exigir_perfil("ADMIN", "ORGANIZADOR"))):

    dados_dict = dados.model_dump()

    payload = {
        "nome": dados_dict.get("titulo"),
        "descricao": dados_dict.get("descricao"),
        "data_evento": str(dados_dict.get("data_evento"))[:10],
        "local": "Auditório Principal",
        "capacidade": dados_dict.get("capacidade"),
        "categoria_id": dados_dict.get("categoria_id"),
        "organizador_id": usuario_atual["id"]
    }

    response = supabase.table("eventos").insert(payload).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Erro ao criar evento.")

    return response.data[0]

@router.put("/{evento_id}", response_model=EventoResponse)
def atualizar_evento(evento_id: int, evento: EventoUpdate, usuario_atual: dict = Depends(exigir_perfil("ADMIN", "ORGANIZADOR"))):
    """Editar dados de um evento (RF06)."""
    evento_resp = supabase.table("eventos").select("*").eq("id", evento_id).execute()
    if not evento_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")

    if usuario_atual["perfil"] == "ORGANIZADOR" and evento_resp.data[0].get("organizador_id") != usuario_atual["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: você só pode editar eventos criados por você.")

    dados_atualizados = {k: v for k, v in evento.model_dump().items() if v is not None}

    if "titulo" in dados_atualizados:
        dados_atualizados["nome"] = dados_atualizados.pop("titulo")

    if "data_evento" in dados_atualizados and dados_atualizados["data_evento"]:
        dados_atualizados["data_evento"] = dados_atualizados["data_evento"].isoformat()[:10]

    if not dados_atualizados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum dado informado para atualização.")

    response = supabase.table("eventos").update(dados_atualizados).eq("id", evento_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
    return response.data[0]

@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_evento(evento_id: int, usuario_atual: dict = Depends(exigir_perfil("ADMIN"))):
    """Remover ou cancelar um evento (RF06, RN04)."""
    response = supabase.table("eventos").delete().eq("id", evento_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
    return None
