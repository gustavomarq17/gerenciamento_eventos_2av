from app.tests.conftest import criar_usuario_com_perfil

EVENTO = {"titulo": "Workshop de FastAPI", "data_evento": "2099-10-15T14:00:00", "capacidade": 10}


def criar_evento(client, cabecalho):
    return client.post("/api/v1/eventos/", json=EVENTO, headers=cabecalho).json()["id"]


def inscrever(client, cabecalho, evento_id, email):
    dados = {"nome_participante": "Participante", "email_participante": email, "evento_id": evento_id}
    return client.post("/api/v1/inscricoes/", json=dados, headers=cabecalho)


def test_cadastro_sempre_cria_participante(client):
    dados = {"nome": "Esperto", "email": "esperto@teste.com", "senha": "senha123", "perfil": "ADMIN"}
    resposta = client.post("/api/v1/auth/register", json=dados)
    assert resposta.status_code == 201
    assert resposta.json()["perfil"] == "PARTICIPANTE"


def test_participante_nao_muda_o_proprio_perfil(client, cabecalho):
    meu_id = client.get("/api/v1/auth/me", headers=cabecalho).json()["id"]
    resposta = client.patch(f"/api/v1/usuarios/{meu_id}/perfil", json={"perfil": "ADMIN"}, headers=cabecalho)
    assert resposta.status_code == 403
    assert client.get("/api/v1/auth/me", headers=cabecalho).json()["perfil"] == "PARTICIPANTE"


def test_organizador_nao_muda_perfil(client, cabecalho, cabecalho_organizador):
    id_participante = client.get("/api/v1/auth/me", headers=cabecalho).json()["id"]
    resposta = client.patch(f"/api/v1/usuarios/{id_participante}/perfil", json={"perfil": "ORGANIZADOR"}, headers=cabecalho_organizador)
    assert resposta.status_code == 403


def test_admin_muda_perfil_e_valor_invalido_da_422(client, cabecalho, cabecalho_admin):
    id_participante = client.get("/api/v1/auth/me", headers=cabecalho).json()["id"]
    resposta = client.patch(f"/api/v1/usuarios/{id_participante}/perfil", json={"perfil": "ORGANIZADOR"}, headers=cabecalho_admin)
    assert resposta.status_code == 200
    assert resposta.json()["perfil"] == "ORGANIZADOR"
    invalido = client.patch(f"/api/v1/usuarios/{id_participante}/perfil", json={"perfil": "SUPERUSUARIO"}, headers=cabecalho_admin)
    assert invalido.status_code == 422


def test_sem_token_retorna_401_e_nao_403(client):
    rotas = [
        ("post", "/api/v1/eventos/"),
        ("put", "/api/v1/eventos/1"),
        ("delete", "/api/v1/eventos/1"),
        ("get", "/api/v1/eventos/"),
        ("post", "/api/v1/inscricoes/"),
        ("delete", "/api/v1/inscricoes/1"),
        ("post", "/api/v1/certificados/"),
        ("get", "/api/v1/usuarios/"),
    ]
    for metodo, rota in rotas:
        resposta = getattr(client, metodo)(rota)
        assert resposta.status_code == 401, f"{metodo.upper()} {rota}"


def test_token_invalido_retorna_401_e_perfil_errado_retorna_403(client, cabecalho):
    invalido = client.post("/api/v1/eventos/", json=EVENTO, headers={"Authorization": "Bearer token-falso"})
    assert invalido.status_code == 401
    sem_permissao = client.post("/api/v1/eventos/", json=EVENTO, headers=cabecalho)
    assert sem_permissao.status_code == 403


def test_usuario_desativado_recebe_401_e_nao_403(client, banco, cabecalho_admin):
    cabecalho_org = criar_usuario_com_perfil(client, banco, "org.desativado@teste.com", "ORGANIZADOR")
    org_id = [u for u in banco.tabelas["usuarios"] if u["email"] == "org.desativado@teste.com"][0]["id"]
    client.patch(f"/api/v1/usuarios/{org_id}/desativar", headers=cabecalho_admin)
    assert client.post("/api/v1/eventos/", json=EVENTO, headers=cabecalho_org).status_code == 401


def test_participante_nao_cria_evento(client, cabecalho):
    assert client.post("/api/v1/eventos/", json=EVENTO, headers=cabecalho).status_code == 403


def test_organizador_cria_evento_e_vira_dono(client, cabecalho_organizador):
    resposta = client.post("/api/v1/eventos/", json=EVENTO, headers=cabecalho_organizador)
    assert resposta.status_code == 201
    meu_id = client.get("/api/v1/auth/me", headers=cabecalho_organizador).json()["id"]
    assert resposta.json()["organizador_id"] == meu_id


def test_organizador_edita_so_o_proprio_evento(client, banco, cabecalho_organizador):
    evento_do_outro = criar_evento(client, criar_usuario_com_perfil(client, banco, "org2@teste.com", "ORGANIZADOR"))
    meu_evento = criar_evento(client, cabecalho_organizador)

    outro = client.put(f"/api/v1/eventos/{evento_do_outro}", json={"titulo": "Invadido"}, headers=cabecalho_organizador)
    assert outro.status_code == 403
    proprio = client.put(f"/api/v1/eventos/{meu_evento}", json={"titulo": "Meu evento editado"}, headers=cabecalho_organizador)
    assert proprio.status_code == 200


def test_admin_edita_evento_de_qualquer_organizador(client, cabecalho_organizador, cabecalho_admin):
    evento_id = criar_evento(client, cabecalho_organizador)
    resposta = client.put(f"/api/v1/eventos/{evento_id}", json={"titulo": "Editado pelo admin"}, headers=cabecalho_admin)
    assert resposta.status_code == 200


def test_participante_nao_edita_evento(client, cabecalho, cabecalho_organizador):
    evento_id = criar_evento(client, cabecalho_organizador)
    assert client.put(f"/api/v1/eventos/{evento_id}", json={"titulo": "X"}, headers=cabecalho).status_code == 403


def test_organizador_nao_exclui_evento_e_admin_exclui(client, cabecalho_organizador, cabecalho_admin):
    evento_id = criar_evento(client, cabecalho_organizador)
    assert client.delete(f"/api/v1/eventos/{evento_id}", headers=cabecalho_organizador).status_code == 403
    assert client.delete(f"/api/v1/eventos/{evento_id}", headers=cabecalho_admin).status_code == 204


def test_todos_os_perfis_listam_eventos(client, cabecalho, cabecalho_organizador, cabecalho_admin):
    for cabecalho_perfil in [cabecalho, cabecalho_organizador, cabecalho_admin]:
        assert client.get("/api/v1/eventos/", headers=cabecalho_perfil).status_code == 200


def test_admin_e_organizador_nao_se_inscrevem(client, cabecalho_organizador, cabecalho_admin):
    evento_id = criar_evento(client, cabecalho_organizador)
    assert inscrever(client, cabecalho_admin, evento_id, "admin@teste.com").status_code == 403
    assert inscrever(client, cabecalho_organizador, evento_id, "organizador@teste.com").status_code == 403


def test_participante_se_inscreve_e_vira_dono(client, cabecalho, cabecalho_organizador):
    evento_id = criar_evento(client, cabecalho_organizador)
    resposta = inscrever(client, cabecalho, evento_id, "maria@teste.com")
    assert resposta.status_code == 201
    meu_id = client.get("/api/v1/auth/me", headers=cabecalho).json()["id"]
    assert resposta.json()["usuario_id"] == meu_id


def test_participante_nao_cancela_inscricao_de_outro(client, cabecalho, cabecalho_participante, cabecalho_organizador):
    evento_id = criar_evento(client, cabecalho_organizador)
    inscricao_do_outro = inscrever(client, cabecalho_participante, evento_id, "participante@teste.com").json()["id"]
    assert client.delete(f"/api/v1/inscricoes/{inscricao_do_outro}", headers=cabecalho).status_code == 403


def test_participante_cancela_a_propria_inscricao(client, cabecalho, cabecalho_organizador):
    evento_id = criar_evento(client, cabecalho_organizador)
    minha = inscrever(client, cabecalho, evento_id, "maria@teste.com").json()["id"]
    assert client.delete(f"/api/v1/inscricoes/{minha}", headers=cabecalho).status_code == 204


def test_organizador_nao_cancela_e_admin_cancela_qualquer(client, cabecalho, cabecalho_organizador, cabecalho_admin):
    evento_id = criar_evento(client, cabecalho_organizador)
    inscricao_id = inscrever(client, cabecalho, evento_id, "maria@teste.com").json()["id"]
    assert client.delete(f"/api/v1/inscricoes/{inscricao_id}", headers=cabecalho_organizador).status_code == 403
    assert client.delete(f"/api/v1/inscricoes/{inscricao_id}", headers=cabecalho_admin).status_code == 204


def test_participante_lista_so_as_proprias_inscricoes(client, cabecalho, cabecalho_participante, cabecalho_organizador):
    evento_id = criar_evento(client, cabecalho_organizador)
    inscrever(client, cabecalho, evento_id, "maria@teste.com")
    inscrever(client, cabecalho_participante, evento_id, "participante@teste.com")

    minhas = client.get("/api/v1/inscricoes/", headers=cabecalho).json()
    assert len(minhas) == 1
    assert minhas[0]["email_participante"] == "maria@teste.com"
    assert len(client.get("/api/v1/inscricoes/", headers=cabecalho_organizador).json()) == 2


def test_presenca_so_pelo_organizador_dono_ou_admin(client, banco, cabecalho, cabecalho_organizador, cabecalho_admin):
    evento_id = criar_evento(client, cabecalho_organizador)
    inscricao_id = inscrever(client, cabecalho, evento_id, "maria@teste.com").json()["id"]
    outro_org = criar_usuario_com_perfil(client, banco, "org2@teste.com", "ORGANIZADOR")

    assert client.patch(f"/api/v1/inscricoes/{inscricao_id}/presenca", headers=cabecalho).status_code == 403
    assert client.patch(f"/api/v1/inscricoes/{inscricao_id}/presenca", headers=outro_org).status_code == 403
    assert client.patch(f"/api/v1/inscricoes/{inscricao_id}/presenca", headers=cabecalho_organizador).status_code == 200
    assert client.patch(f"/api/v1/inscricoes/{inscricao_id}/presenca", headers=cabecalho_admin).status_code == 200


def test_certificado_participante_nao_emite_mas_consulta(client, cabecalho, cabecalho_organizador):
    evento_id = criar_evento(client, cabecalho_organizador)
    inscricao_id = inscrever(client, cabecalho, evento_id, "maria@teste.com").json()["id"]
    client.patch(f"/api/v1/inscricoes/{inscricao_id}/presenca", headers=cabecalho_organizador)

    assert client.post("/api/v1/certificados/", json={"inscricao_id": inscricao_id}, headers=cabecalho).status_code == 403
    emitido = client.post("/api/v1/certificados/", json={"inscricao_id": inscricao_id}, headers=cabecalho_organizador)
    assert emitido.status_code == 201

    codigo = emitido.json()["codigo_validador"]
    assert client.get(f"/api/v1/certificados/{codigo}", headers=cabecalho).status_code == 200
    assert client.get("/api/v1/certificados/", headers=cabecalho).status_code == 403
    assert client.delete(f"/api/v1/certificados/{emitido.json()['id']}", headers=cabecalho_organizador).status_code == 403


def test_usuarios_proprios_dados_e_gestao_pelo_admin(client, banco, cabecalho, cabecalho_participante, cabecalho_admin):
    meu_id = client.get("/api/v1/auth/me", headers=cabecalho).json()["id"]
    id_outro = client.get("/api/v1/auth/me", headers=cabecalho_participante).json()["id"]

    assert client.get("/api/v1/usuarios/", headers=cabecalho).status_code == 403
    assert client.get(f"/api/v1/usuarios/{meu_id}", headers=cabecalho).status_code == 200
    assert client.get(f"/api/v1/usuarios/{id_outro}", headers=cabecalho).status_code == 403
    assert client.put(f"/api/v1/usuarios/{id_outro}", json={"nome": "Invadido"}, headers=cabecalho).status_code == 403
    assert client.patch(f"/api/v1/usuarios/{id_outro}/desativar", headers=cabecalho).status_code == 403
    assert client.get("/api/v1/usuarios/", headers=cabecalho_admin).status_code == 200


def test_categorias_so_admin_gerencia(client, cabecalho, cabecalho_organizador, cabecalho_admin):
    nova = {"nome": "Palestra"}
    assert client.post("/api/v1/categorias/", json=nova, headers=cabecalho).status_code == 403
    assert client.post("/api/v1/categorias/", json=nova, headers=cabecalho_organizador).status_code == 403
    assert client.post("/api/v1/categorias/", json=nova, headers=cabecalho_admin).status_code == 201
    assert client.get("/api/v1/categorias/", headers=cabecalho).status_code == 200
