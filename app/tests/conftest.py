import os
from datetime import datetime, timezone

os.environ["SUPABASE_URL"] = "http://localhost:54321"
os.environ["SUPABASE_KEY"] = "chave-de-teste"
os.environ["JWT_SECRET_KEY"] = "segredo-somente-para-testes-com-32-bytes-ou-mais"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.routers import auth, categorias, eventos, inscricoes, lista_espera, usuarios, certificados
from app.utils import security

PADROES = {
    "eventos": {"status": "ATIVO"},
    "inscricoes": {"status": "ATIVA", "presente": False},
    "usuarios": {"ativo": True, "perfil": "PARTICIPANTE"},
}


class Resposta:
    """Imita o objeto devolvido pelo .execute() do supabase-py."""
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class ConsultaFalsa:
    """Imita supabase.table(...).select/insert/update/delete/eq/order/limit/execute."""
    def __init__(self, banco, tabela):
        self.banco = banco
        self.tabela = tabela
        self.acao = "select"
        self.valores = None
        self.filtros = []
        self.ordem = None
        self.limite = None
        self.contar = False

    def select(self, *colunas, count=None):
        self.acao = "select"
        self.contar = count is not None
        return self

    def insert(self, valores):
        self.acao = "insert"
        self.valores = valores
        return self

    def update(self, valores):
        self.acao = "update"
        self.valores = valores
        return self

    def delete(self):
        self.acao = "delete"
        return self

    def eq(self, coluna, valor):
        self.filtros.append((coluna, valor))
        return self

    def order(self, coluna, desc=False):
        self.ordem = (coluna, desc)
        return self

    def limit(self, quantidade):
        self.limite = quantidade
        return self

    def execute(self):
        if self.banco.sem_conexao:
            raise httpx.ConnectError("[Errno 11001] getaddrinfo failed")

        linhas = self.banco.tabelas.setdefault(self.tabela, [])

        if self.acao == "insert":
            nova = dict(PADROES.get(self.tabela, {}))
            nova.update(self.valores)
            self.banco.ultimo_id += 1
            nova["id"] = self.banco.ultimo_id
            nova["created_at"] = datetime.now(timezone.utc).isoformat()
            if self.tabela == "lista_espera":
                nova["data_criacao"] = nova["created_at"]
            linhas.append(nova)
            return Resposta([dict(nova)])

        encontradas = [l for l in linhas if all(str(l.get(c)) == str(v) for c, v in self.filtros)]

        if self.acao == "update":
            for linha in encontradas:
                linha.update(self.valores)
            return Resposta([dict(l) for l in encontradas])

        if self.acao == "delete":
            for linha in encontradas:
                linhas.remove(linha)
            return Resposta([dict(l) for l in encontradas])

        if self.ordem:
            coluna, desc = self.ordem
            encontradas = sorted(encontradas, key=lambda l: l[coluna], reverse=desc)
        if self.limite is not None:
            encontradas = encontradas[:self.limite]
        return Resposta([dict(l) for l in encontradas], count=len(encontradas) if self.contar else None)


class SupabaseFalso:
    def __init__(self):
        self.tabelas = {}
        self.ultimo_id = 0
        self.sem_conexao = False

    def table(self, nome):
        return ConsultaFalsa(self, nome)


@pytest.fixture
def banco(monkeypatch):
    """Troca o supabase real pelo falso em todos os módulos que o importam."""
    falso = SupabaseFalso()
    for modulo in [auth, categorias, eventos, inscricoes, lista_espera, usuarios, certificados, security]:
        monkeypatch.setattr(modulo, "supabase", falso)
    return falso


@pytest.fixture
def client(banco):
    return TestClient(app)


def cadastrar_e_logar(client, email="maria@teste.com", senha="senha123", nome="Maria"):
    """Cadastra um usuário, faz login e devolve o token JWT."""
    client.post("/api/v1/auth/register", json={"nome": nome, "email": email, "senha": senha})
    resposta = client.post("/api/v1/auth/login", data={"username": email, "password": senha})
    return resposta.json()["access_token"]


@pytest.fixture
def cabecalho(client):
    """Cabeçalho Authorization com um token válido."""
    token = cadastrar_e_logar(client)
    return {"Authorization": f"Bearer {token}"}


def criar_usuario_com_perfil(client, banco, email, perfil):
    client.post("/api/v1/auth/register", json={"nome": perfil.title(), "email": email, "senha": "senha123"})
    for usuario in banco.tabelas["usuarios"]:
        if usuario["email"] == email:
            usuario["perfil"] = perfil
    resposta = client.post("/api/v1/auth/login", data={"username": email, "password": "senha123"})
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


@pytest.fixture
def cabecalho_admin(client, banco):
    return criar_usuario_com_perfil(client, banco, "admin@teste.com", "ADMIN")


@pytest.fixture
def cabecalho_organizador(client, banco):
    return criar_usuario_com_perfil(client, banco, "organizador@teste.com", "ORGANIZADOR")


@pytest.fixture
def cabecalho_participante(client, banco):
    return criar_usuario_com_perfil(client, banco, "participante@teste.com", "PARTICIPANTE")
