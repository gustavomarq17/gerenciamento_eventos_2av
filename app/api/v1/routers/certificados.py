import uuid
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.certificado import CertificadoCreate, CertificadoResponse
from app.utils.security import obter_usuario_atual, exigir_perfil
from app.database.connection import supabase

router = APIRouter(prefix="/certificados", tags=["Certificados"])

@router.post("/", response_model=CertificadoResponse, status_code=status.HTTP_201_CREATED)
def emitir_certificado(dados: CertificadoCreate, usuario_atual: dict = Depends(exigir_perfil("ADMIN", "ORGANIZADOR"))):
    """Emitir certificado para uma inscrição confirmada e com presença registrada (RF10, RN07)."""

    inscricao_resp = supabase.table("inscricoes").select("*").eq("id", dados.inscricao_id).execute()
    if not inscricao_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada.")

    inscricao = inscricao_resp.data[0]

    if inscricao.get("status") != "ATIVA":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A inscrição não está confirmada.")
    if not inscricao.get("presente"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A presença do participante não foi registrada.")

    existente = supabase.table("certificados").select("id").eq("inscricao_id", dados.inscricao_id).execute()
    if existente.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe um certificado para esta inscrição.")

    novo_certificado = {
        "inscricao_id": dados.inscricao_id,
        "codigo_validador": str(uuid.uuid4())
    }

    response = supabase.table("certificados").insert(novo_certificado).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao emitir certificado.")
    return response.data[0]

@router.get("/", response_model=list[CertificadoResponse])
def listar_certificados(usuario_atual: dict = Depends(exigir_perfil("ADMIN", "ORGANIZADOR"))):
    """Listar todos os certificados emitidos."""
    response = supabase.table("certificados").select("*").execute()
    return response.data

@router.get("/{codigo_validador}", response_model=CertificadoResponse)
def validar_certificado(codigo_validador: UUID, usuario_atual: dict = Depends(obter_usuario_atual)):
    """Consultar e validar um certificado pelo código validador (RF11).
    Código fora do formato UUID retorna 422; código inexistente retorna 404."""
    response = supabase.table("certificados").select("*").eq("codigo_validador", str(codigo_validador)).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificado não encontrado ou código inválido.")
    return response.data[0]

@router.delete("/{certificado_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_certificado(certificado_id: int, usuario_atual: dict = Depends(exigir_perfil("ADMIN"))):
    """Excluir um certificado."""
    response = supabase.table("certificados").delete().eq("id", certificado_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificado não encontrado.")
    return None
