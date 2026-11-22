import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.database.connection import supabase
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def hash_senha(senha: str) -> str:
    """Gera o hash seguro da senha."""
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Verifica se a senha bate com o hash armazenado."""
    try:
        return bcrypt.checkpw(senha_plana.encode("utf-8"), senha_hash.encode("utf-8"))
    except (ValueError, AttributeError):
        return False

def criar_token_acesso(data: dict) -> str:
    """Gera o token JWT com tempo de expiração."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def obter_usuario_atual(token: str = Depends(oauth2_scheme)):
    """Valida o token JWT e retorna o usuário autenticado (retorna 401 se falhar)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais de autenticação inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    response = supabase.table("usuarios").select("*").eq("email", email).execute()
    if not response.data:
        raise credentials_exception
    usuario = response.data[0]
    if usuario.get("ativo") is False:
        raise credentials_exception
    return usuario

def exigir_perfil(*perfis_permitidos):
    def verificar_perfil(usuario_atual: dict = Depends(obter_usuario_atual)):
        if usuario_atual.get("perfil") not in perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: seu perfil não tem permissão para esta ação.",
            )
        return usuario_atual
    return verificar_perfil
