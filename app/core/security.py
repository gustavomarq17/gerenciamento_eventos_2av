import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "chave_secreta_padrao")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Compara uma senha em texto puro com o hash salvo no banco."""
    return pwd_context.verify(senha_plana, senha_hash)

def gerar_hash_senha(senha: str) -> str:
    """Gera um hash seguro (bcrypt) a partir de uma senha em texto puro."""
    return pwd_context.hash(senha)

def criar_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Gera o token JWT contendo os dados do usuário e tempo de expiração."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decodificar_token(token: str) -> Optional[dict]:
    """Valida a assinatura e a expiração do token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
