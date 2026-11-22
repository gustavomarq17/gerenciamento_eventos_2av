from fastapi import FastAPI
import httpx
from fastapi import Request
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from app.api.v1.routers import eventos, inscricoes, categorias, auth, lista_espera, usuarios, certificados

app = FastAPI(
    title="API de Gerenciamento de Eventos Acadêmicos",
    version="1.0.0",
    description="API RESTful segura com autenticação JWT e controle de acesso."
)

app.include_router(categorias.router, prefix="/api/v1")
app.include_router(eventos.router, prefix="/api/v1")
app.include_router(inscricoes.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(lista_espera.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(certificados.router, prefix="/api/v1")

@app.exception_handler(httpx.HTTPError)
def erro_conexao_banco(request: Request, exc: httpx.HTTPError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Não foi possível conectar ao banco de dados (Supabase). Verifique a internet/rede."},
    )

@app.exception_handler(APIError)
def erro_banco(request: Request, exc: APIError):
    if exc.code == "23505":
        mensagem = "Registro duplicado."
    else:
        mensagem = f"Erro no banco de dados: {exc.message}"
    return JSONResponse(status_code=400, content={"detail": mensagem})

@app.get("/")
def root():
    return {"message": "API de Eventos Acadêmicos rodando com sucesso!"}
