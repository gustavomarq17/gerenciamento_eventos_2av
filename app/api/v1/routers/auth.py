from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.usuarios import UsuarioCreate, UsuarioResponse, LoginRequest, Token
from app.utils.security import hash_senha, verificar_senha, criar_token_acesso, obter_usuario_atual
from app.database.connection import supabase

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(dados: UsuarioCreate):
    
    existe = supabase.table("usuarios").select("*").eq("email", dados.email).execute()
    if existe.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado.")
    
   
    senha_segura = hash_senha(dados.senha)
    
    novo_usuario = {
        "nome": dados.nome,
        "email": dados.email,
        "senha_hash": senha_segura
    }
    
    response = supabase.table("usuarios").insert(novo_usuario).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao cadastrar usuário.")
        
    return response.data[0]

@router.post("/login", response_model=Token)
def login(dados: LoginRequest):
    
    response = supabase.table("usuarios").select("*").eq("email", dados.email).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos.")
    
    usuario = response.data[0]
    
    
    if not verificar_senha(dados.senha, usuario["senha_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos.")
    
   
    token = criar_token_acesso({"sub": usuario["email"]})
    
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UsuarioResponse)
def consultar_usuario_autenticado(usuario_atual: dict = Depends(obter_usuario_atual)):
    """Retorna os dados do usuário logado (Rota protegida)."""
    return usuario_atual