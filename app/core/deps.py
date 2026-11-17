from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.database.connection import supabase  
from app.core.security import decodificar_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def obter_usuario_atual(token: str = Depends(oauth2_scheme)):
    """Valida o token JWT e busca os dados do usuário direto no Supabase."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decodificar_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
        
  
    try:
        response = supabase.table("usuarios").select("*").eq("email", email).execute()
        usuarios = response.data
        if not usuarios:
            raise credentials_exception
        return usuarios[0]  
    except Exception:
        raise credentials_exception

class VerificarPerfil:
    """Restringe o acesso à rota com base no perfil do usuário (Exige 403 se não permitido)."""
    def __init__(self, perfis_permitidos: list):
        self.perfis_permitidos = perfis_permitidos

    def __call__(self, usuario: dict = Depends(obter_usuario_atual)):
        if usuario.get("perfil") not in self.perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: permissão insuficiente."
            )
        return usuario