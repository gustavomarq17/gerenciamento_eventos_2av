# [2AV] Testes que garantem que os CRUDs da 1ª Unidade (categorias e eventos) continuam respondendo.

def test_crud_categorias(client):
    criada = client.post("/api/v1/categorias/", json={"nome": "Palestra", "descricao": "Palestras gerais"})
    assert criada.status_code == 201
    categoria_id = criada.json()["id"]

    assert client.get("/api/v1/categorias/").status_code == 200
    assert client.get(f"/api/v1/categorias/{categoria_id}").json()["nome"] == "Palestra"

    editada = client.put(f"/api/v1/categorias/{categoria_id}", json={"nome": "Workshop"})
    assert editada.status_code == 200
    assert editada.json()["nome"] == "Workshop"

    assert client.delete(f"/api/v1/categorias/{categoria_id}").status_code == 204
    assert client.get(f"/api/v1/categorias/{categoria_id}").status_code == 404


def test_listar_eventos_com_colunas_reais_e_data_passada(client, banco):
    # Linha no formato real da tabela (nome, local, data como date). Antes dava 500.
    banco.tabelas["eventos"] = [{
        "id": 1, "created_at": "2026-01-01T00:00:00+00:00", "nome": "Semana Acadêmica",
        "descricao": None, "data_evento": "2025-05-10", "local": "Auditório", "capacidade": 50,
        "categoria_id": None, "status": "CONCLUIDO",
    }]
    resposta = client.get("/api/v1/eventos/")
    assert resposta.status_code == 200
    assert resposta.json()[0]["nome"] == "Semana Acadêmica"
    assert client.get("/api/v1/eventos/1").status_code == 200
    assert client.get("/api/v1/eventos/999").status_code == 404


def test_editar_e_excluir_evento(client, banco, cabecalho):
    evento_id = client.post(
        "/api/v1/eventos/", json={"titulo": "Workshop", "data_evento": "2099-10-15T14:00:00"}, headers=cabecalho
    ).json()["id"]

    editado = client.put(f"/api/v1/eventos/{evento_id}", json={"titulo": "Workshop Avançado", "data_evento": "2099-11-01T10:00:00"})
    assert editado.status_code == 200
    assert editado.json()["nome"] == "Workshop Avançado"
    assert banco.tabelas["eventos"][0]["data_evento"] == "2099-11-01"
    assert "titulo" not in banco.tabelas["eventos"][0]

    assert client.delete(f"/api/v1/eventos/{evento_id}").status_code == 204


def test_criar_evento_com_data_passada_retorna_422(client, cabecalho):
    resposta = client.post("/api/v1/eventos/", json={"titulo": "Antigo", "data_evento": "2000-01-01T10:00:00"}, headers=cabecalho)
    assert resposta.status_code == 422


def test_lista_espera_duplicada_retorna_400(client, banco):
    banco.tabelas["eventos"] = [{"id": 1, "nome": "Evento", "created_at": "2026-01-01T00:00:00+00:00"}]
    dados = {"participante_id": 1, "evento_id": 1, "nome_participante": "A", "email_participante": "a@email.com"}
    assert client.post("/api/v1/lista-espera/", json=dados).status_code == 201
    assert client.post("/api/v1/lista-espera/", json=dados).status_code == 400
