# [2AV] Testes do CRUD de usuários (RF03): listar, consultar, editar e desativar.

def test_rotas_de_usuarios_sem_token_retornam_401(client):
    assert client.get("/api/v1/usuarios/").status_code == 401
    assert client.get("/api/v1/usuarios/1").status_code == 401
    assert client.put("/api/v1/usuarios/1", json={"nome": "X"}).status_code == 401
    assert client.patch("/api/v1/usuarios/1/desativar").status_code == 401


def test_listar_e_consultar_sem_senha(client, cabecalho):
    lista = client.get("/api/v1/usuarios/", headers=cabecalho)
    assert lista.status_code == 200
    assert len(lista.json()) == 1
    for usuario in lista.json():
        assert "senha" not in usuario
        assert "senha_hash" not in usuario

    usuario_id = lista.json()[0]["id"]
    consulta = client.get(f"/api/v1/usuarios/{usuario_id}", headers=cabecalho)
    assert consulta.status_code == 200
    assert consulta.json()["ativo"] is True
    assert "senha_hash" not in consulta.json()


def test_consultar_usuario_inexistente_retorna_404(client, cabecalho):
    assert client.get("/api/v1/usuarios/999", headers=cabecalho).status_code == 404


def test_editar_usuario(client, cabecalho):
    usuario_id = client.get("/api/v1/auth/me", headers=cabecalho).json()["id"]
    resposta = client.put(f"/api/v1/usuarios/{usuario_id}", json={"nome": "Maria Silva"}, headers=cabecalho)
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Maria Silva"
    assert "senha_hash" not in resposta.json()

    assert client.put(f"/api/v1/usuarios/{usuario_id}", json={}, headers=cabecalho).status_code == 400
    assert client.put("/api/v1/usuarios/999", json={"nome": "X"}, headers=cabecalho).status_code == 404


def test_editar_usuario_com_email_de_outro_retorna_400(client, cabecalho):
    client.post("/api/v1/auth/register", json={"nome": "João", "email": "joao@teste.com", "senha": "senha123"})
    usuario_id = client.get("/api/v1/auth/me", headers=cabecalho).json()["id"]
    resposta = client.put(f"/api/v1/usuarios/{usuario_id}", json={"email": "joao@teste.com"}, headers=cabecalho)
    assert resposta.status_code == 400


def test_desativar_usuario_bloqueia_login_e_token(client, banco, cabecalho):
    client.post("/api/v1/auth/register", json={"nome": "João", "email": "joao@teste.com", "senha": "senha123"})
    token_joao = client.post("/api/v1/auth/login", data={"username": "joao@teste.com", "password": "senha123"}).json()["access_token"]
    joao_id = [u for u in banco.tabelas["usuarios"] if u["email"] == "joao@teste.com"][0]["id"]

    resposta = client.patch(f"/api/v1/usuarios/{joao_id}/desativar", headers=cabecalho)
    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False
    assert "senha_hash" not in resposta.json()

    # O registro continua no banco (desativado, não apagado).
    assert len(banco.tabelas["usuarios"]) == 2

    # Usuário desativado não faz login e o token antigo deixa de valer.
    login = client.post("/api/v1/auth/login", data={"username": "joao@teste.com", "password": "senha123"})
    assert login.status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_joao}"}).status_code == 401

    assert client.patch("/api/v1/usuarios/999/desativar", headers=cabecalho).status_code == 404
