from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.usuarios import UsuarioResponse, UsuarioUpdate, PerfilUpdate
from app.utils.security import obter_usuario_atual, exigir_perfil
from app.database.connection import supabase

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

COLUNAS_PUBLICAS = "id, created_at, nome, email, ativo, perfil"

@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(usuario_atual: dict = Depends(exigir_perfil("ADMIN"))):
    """Listar todos os usuários (RF03)."""
    response = supabase.table("usuarios").select(COLUNAS_PUBLICAS).execute()
    return response.data

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obter_usuario(usuario_id: int, usuario_atual: dict = Depends(obter_usuario_atual)):
    """Consultar um usuário pelo ID (RF03)."""
    if usuario_atual["perfil"] != "ADMIN" and usuario_atual["id"] != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: você só pode ver os seus próprios dados.")

    response = supabase.table("usuarios").select(COLUNAS_PUBLICAS).eq("id", usuario_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return response.data[0]

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(usuario_id: int, usuario: UsuarioUpdate, usuario_atual: dict = Depends(obter_usuario_atual)):
    """Editar nome e/ou e-mail de um usuário (RF03)."""
    if usuario_atual["perfil"] != "ADMIN" and usuario_atual["id"] != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: você só pode editar os seus próprios dados.")

    dados = {k: v for k, v in usuario.model_dump().items() if v is not None}
    if not dados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum dado informado para atualização.")

    if "email" in dados:
        existe = supabase.table("usuarios").select("id").eq("email", dados["email"]).execute()
        if existe.data and existe.data[0]["id"] != usuario_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado.")

    response = supabase.table("usuarios").update(dados).eq("id", usuario_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return response.data[0]

@router.patch("/{usuario_id}/desativar", response_model=UsuarioResponse)
def desativar_usuario(usuario_id: int, usuario_atual: dict = Depends(exigir_perfil("ADMIN"))):
    """Desativar um usuário (RF03). O registro NÃO é apagado, só fica com ativo = false."""
    response = supabase.table("usuarios").update({"ativo": False}).eq("id", usuario_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return response.data[0]

@router.patch("/{usuario_id}/perfil", response_model=UsuarioResponse)
def alterar_perfil(usuario_id: int, dados: PerfilUpdate, usuario_atual: dict = Depends(exigir_perfil("ADMIN"))):
    """Alterar o perfil de um usuário (ADMIN, ORGANIZADOR ou PARTICIPANTE)."""
    response = supabase.table("usuarios").update({"perfil": dados.perfil}).eq("id", usuario_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return response.data[0]
