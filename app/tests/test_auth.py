from datetime import datetime, timedelta, timezone
import jwt

SEGREDO_TESTE = "segredo-somente-para-testes-com-32-bytes-ou-mais"
EVENTO = {"titulo": "Workshop de FastAPI", "data_evento": "2099-10-15T14:00:00", "capacidade": 10}


def test_cadastro_retorna_201_sem_senha(client, banco):
    resposta = client.post("/api/v1/auth/register", json={"nome": "Ana", "email": "ana@teste.com", "senha": "senha123"})
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email"] == "ana@teste.com"
    assert "senha" not in corpo
    assert "senha_hash" not in corpo
    salvo = banco.tabelas["usuarios"][0]["senha_hash"]
    assert salvo.startswith("$2b$")
    assert salvo != "senha123"


def test_cadastro_email_duplicado_retorna_400(client):
    dados = {"nome": "Ana", "email": "ana@teste.com", "senha": "senha123"}
    client.post("/api/v1/auth/register", json=dados)
    resposta = client.post("/api/v1/auth/register", json=dados)
    assert resposta.status_code == 400


def test_cadastro_email_invalido_retorna_422(client):
    resposta = client.post("/api/v1/auth/register", json={"nome": "Ana", "email": "nao-e-email", "senha": "senha123"})
    assert resposta.status_code == 422


def test_cadastro_senha_maior_que_72_bytes_retorna_422(client):
    resposta = client.post("/api/v1/auth/register", json={"nome": "Ana", "email": "ana@teste.com", "senha": "a" * 73})
    assert resposta.status_code == 422


def test_login_correto_retorna_token(client):
    client.post("/api/v1/auth/register", json={"nome": "Ana", "email": "ana@teste.com", "senha": "senha123"})
    resposta = client.post("/api/v1/auth/login", data={"username": "ana@teste.com", "password": "senha123"})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["perfil"] == "PARTICIPANTE"
    payload = jwt.decode(corpo["access_token"], SEGREDO_TESTE, algorithms=["HS256"])
    assert payload["sub"] == "ana@teste.com"
    assert "exp" in payload


def test_login_senha_errada_retorna_401(client):
    client.post("/api/v1/auth/register", json={"nome": "Ana", "email": "ana@teste.com", "senha": "senha123"})
    resposta = client.post("/api/v1/auth/login", data={"username": "ana@teste.com", "password": "errada"})
    assert resposta.status_code == 401


def test_login_email_inexistente_retorna_401(client):
    resposta = client.post("/api/v1/auth/login", data={"username": "ninguem@teste.com", "password": "senha123"})
    assert resposta.status_code == 401


def test_me_com_token_valido_retorna_usuario(client, cabecalho):
    resposta = client.get("/api/v1/auth/me", headers=cabecalho)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["email"] == "maria@teste.com"
    assert "senha_hash" not in corpo
    assert corpo["perfil"] == "PARTICIPANTE"


def test_me_sem_token_retorna_401(client):
    resposta = client.get("/api/v1/auth/me")
    assert resposta.status_code == 401
    assert resposta.headers["WWW-Authenticate"] == "Bearer"


def test_me_token_invalido_retorna_401(client):
    resposta = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token-qualquer"})
    assert resposta.status_code == 401
    assert resposta.headers["WWW-Authenticate"] == "Bearer"


def test_me_token_com_outra_chave_retorna_401(client, cabecalho):
    falso = jwt.encode({"sub": "maria@teste.com", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, "outra-chave-de-um-atacante-com-mais-de-32-bytes", algorithm="HS256")
    resposta = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {falso}"})
    assert resposta.status_code == 401


def test_me_token_expirado_retorna_401(client, cabecalho):
    expirado = jwt.encode({"sub": "maria@teste.com", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, SEGREDO_TESTE, algorithm="HS256")
    resposta = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expirado}"})
    assert resposta.status_code == 401
    assert resposta.headers["WWW-Authenticate"] == "Bearer"


def test_criar_evento_sem_token_retorna_401(client):
    resposta = client.post("/api/v1/eventos/", json=EVENTO)
    assert resposta.status_code == 401


def test_criar_evento_com_token_invalido_retorna_401(client):
    resposta = client.post("/api/v1/eventos/", json=EVENTO, headers={"Authorization": "Bearer abc.def.ghi"})
    assert resposta.status_code == 401


def test_criar_evento_com_token_valido_retorna_201(client, cabecalho_organizador):
    resposta = client.post("/api/v1/eventos/", json=EVENTO, headers=cabecalho_organizador)
    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Workshop de FastAPI"


def test_inscricao_sem_token_retorna_401(client):
    resposta = client.post("/api/v1/inscricoes/", json={"nome_participante": "Ana", "email_participante": "ana@teste.com", "evento_id": 1})
    assert resposta.status_code == 401


def test_inscricao_com_token_valido_retorna_201(client, cabecalho, cabecalho_organizador):
    evento_id = client.post("/api/v1/eventos/", json=EVENTO, headers=cabecalho_organizador).json()["id"]
    resposta = client.post(
        "/api/v1/inscricoes/",
        json={"nome_participante": "Ana", "email_participante": "ana@teste.com", "evento_id": evento_id},
        headers=cabecalho,
    )
    assert resposta.status_code == 201
    assert resposta.json()["status"] == "ATIVA"


def test_falha_de_rede_retorna_503(client, banco, cabecalho):
    banco.sem_conexao = True
    resposta = client.get("/api/v1/categorias/", headers=cabecalho)
    assert resposta.status_code == 503


def test_erro_do_banco_retorna_400(client, banco, monkeypatch, cabecalho):
    from postgrest.exceptions import APIError

    def explodir(*args, **kwargs):
        raise APIError({"message": "column eventos.titulo does not exist", "code": "42703"})

    monkeypatch.setattr(banco, "table", explodir)
    resposta = client.get("/api/v1/eventos/", headers=cabecalho)
    assert resposta.status_code == 400
    assert "does not exist" in resposta.json()["detail"]
