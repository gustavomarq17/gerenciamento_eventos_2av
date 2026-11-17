import os
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.database.connection import supabase

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sua_chave_secreta_super_segura_padrao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def hash_senha(senha: str) -> str:
    """Gera o hash seguro da senha."""
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Verifica se a senha bate com o hash armazenado."""
    return pwd_context.verify(senha_plana, senha_hash)

def criar_token_acesso(data: dict) -> str:
    """Gera o token JWT com tempo de expiração."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def obter_usuario_atual(token: str = Depends(oauth2_scheme)):
    """Valida o token JWT e retorna o usuário autenticado (retorna 401 se falhar)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais de autenticação inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    response = supabase.table("usuarios").select("*").eq("email", email).execute()
    if not response.data:
        raise credentials_exception
    return response.data[0]