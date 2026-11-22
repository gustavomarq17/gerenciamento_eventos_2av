def test_crud_categorias(client, cabecalho_admin):
    criada = client.post("/api/v1/categorias/", json={"nome": "Palestra", "descricao": "Palestras gerais"}, headers=cabecalho_admin)
    assert criada.status_code == 201
    categoria_id = criada.json()["id"]

    assert client.get("/api/v1/categorias/", headers=cabecalho_admin).status_code == 200
    assert client.get(f"/api/v1/categorias/{categoria_id}", headers=cabecalho_admin).json()["nome"] == "Palestra"

    editada = client.put(f"/api/v1/categorias/{categoria_id}", json={"nome": "Workshop"}, headers=cabecalho_admin)
    assert editada.status_code == 200
    assert editada.json()["nome"] == "Workshop"

    assert client.delete(f"/api/v1/categorias/{categoria_id}", headers=cabecalho_admin).status_code == 204
    assert client.get(f"/api/v1/categorias/{categoria_id}", headers=cabecalho_admin).status_code == 404


def test_listar_eventos_com_colunas_reais_e_data_passada(client, banco, cabecalho):
    banco.tabelas["eventos"] = [{
        "id": 1, "created_at": "2026-01-01T00:00:00+00:00", "nome": "Semana Acadêmica",
        "descricao": None, "data_evento": "2025-05-10", "local": "Auditório", "capacidade": 50,
        "categoria_id": None, "status": "CONCLUIDO",
    }]
    resposta = client.get("/api/v1/eventos/", headers=cabecalho)
    assert resposta.status_code == 200
    assert resposta.json()[0]["nome"] == "Semana Acadêmica"
    assert client.get("/api/v1/eventos/1", headers=cabecalho).status_code == 200
    assert client.get("/api/v1/eventos/999", headers=cabecalho).status_code == 404


def test_editar_e_excluir_evento(client, banco, cabecalho_organizador, cabecalho_admin):
    evento_id = client.post(
        "/api/v1/eventos/", json={"titulo": "Workshop", "data_evento": "2099-10-15T14:00:00"}, headers=cabecalho_organizador
    ).json()["id"]

    editado = client.put(
        f"/api/v1/eventos/{evento_id}", json={"titulo": "Workshop Avançado", "data_evento": "2099-11-01T10:00:00"}, headers=cabecalho_organizador
    )
    assert editado.status_code == 200
    assert editado.json()["nome"] == "Workshop Avançado"
    assert banco.tabelas["eventos"][0]["data_evento"] == "2099-11-01"
    assert "titulo" not in banco.tabelas["eventos"][0]

    assert client.delete(f"/api/v1/eventos/{evento_id}", headers=cabecalho_admin).status_code == 204


def test_criar_evento_com_data_passada_retorna_422(client, cabecalho_organizador):
    resposta = client.post("/api/v1/eventos/", json={"titulo": "Antigo", "data_evento": "2000-01-01T10:00:00"}, headers=cabecalho_organizador)
    assert resposta.status_code == 422


def test_lista_espera_duplicada_retorna_400(client, banco, cabecalho):
    banco.tabelas["eventos"] = [{"id": 1, "nome": "Evento", "created_at": "2026-01-01T00:00:00+00:00"}]
    dados = {"participante_id": 1, "evento_id": 1, "nome_participante": "A", "email_participante": "a@email.com"}
    assert client.post("/api/v1/lista-espera/", json=dados, headers=cabecalho).status_code == 201
    assert client.post("/api/v1/lista-espera/", json=dados, headers=cabecalho).status_code == 400
