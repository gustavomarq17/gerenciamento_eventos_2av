def criar_evento(banco, status="ATIVO", capacidade=50):
    banco.tabelas.setdefault("eventos", []).append(
        {"id": 1, "nome": "Palestra Teste", "status": status, "capacidade": capacidade, "created_at": "2026-01-01T00:00:00+00:00"}
    )


def test_realizar_inscricao_evento_inativo(client, banco, cabecalho):
    criar_evento(banco, status="CANCELADO")
    payload = {"nome_participante": "Teste", "email_participante": "teste@email.com", "evento_id": 1}

    response = client.post("/api/v1/inscricoes/", json=payload, headers=cabecalho)

    assert response.status_code == 400
    assert "Não é possível se inscrever em eventos inativos" in response.json()["detail"]


def test_inscricao_evento_inexistente_retorna_404(client, cabecalho):
    payload = {"nome_participante": "Teste", "email_participante": "teste@email.com", "evento_id": 999}
    response = client.post("/api/v1/inscricoes/", json=payload, headers=cabecalho)
    assert response.status_code == 404


def test_inscricao_duplicada_retorna_400(client, banco, cabecalho):
    criar_evento(banco)
    payload = {"nome_participante": "Teste", "email_participante": "teste@email.com", "evento_id": 1}
    client.post("/api/v1/inscricoes/", json=payload, headers=cabecalho)
    response = client.post("/api/v1/inscricoes/", json=payload, headers=cabecalho)
    assert response.status_code == 400


def test_inscricao_evento_lotado_retorna_400(client, banco, cabecalho):
    criar_evento(banco, capacidade=1)
    client.post("/api/v1/inscricoes/", json={"nome_participante": "A", "email_participante": "a@email.com", "evento_id": 1}, headers=cabecalho)
    response = client.post("/api/v1/inscricoes/", json={"nome_participante": "B", "email_participante": "b@email.com", "evento_id": 1}, headers=cabecalho)
    assert response.status_code == 400
    assert "Capacidade" in response.json()["detail"]


def test_listar_inscricoes(client, banco, cabecalho):
    criar_evento(banco)
    client.post("/api/v1/inscricoes/", json={"nome_participante": "A", "email_participante": "a@email.com", "evento_id": 1}, headers=cabecalho)
    response = client.get("/api/v1/inscricoes/", headers=cabecalho)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_marcar_presenca(client, banco, cabecalho, cabecalho_admin):
    criar_evento(banco)
    inscricao_id = client.post(
        "/api/v1/inscricoes/", json={"nome_participante": "A", "email_participante": "a@email.com", "evento_id": 1}, headers=cabecalho
    ).json()["id"]

    assert client.patch(f"/api/v1/inscricoes/{inscricao_id}/presenca").status_code == 401
    response = client.patch(f"/api/v1/inscricoes/{inscricao_id}/presenca", headers=cabecalho_admin)
    assert response.status_code == 200
    assert response.json()["presente"] is True
    assert client.patch("/api/v1/inscricoes/999/presenca", headers=cabecalho_admin).status_code == 404


def test_cancelar_inscricao_promove_lista_espera(client, banco, cabecalho, cabecalho_participante):
    criar_evento(banco, capacidade=1)
    inscricao_id = client.post(
        "/api/v1/inscricoes/", json={"nome_participante": "A", "email_participante": "a@email.com", "evento_id": 1}, headers=cabecalho
    ).json()["id"]
    fila = client.post(
        "/api/v1/lista-espera/",
        json={"participante_id": 999, "evento_id": 1, "nome_participante": "B", "email_participante": "b@email.com"},
        headers=cabecalho_participante,
    )
    assert fila.status_code == 201
    id_da_fila = client.get("/api/v1/auth/me", headers=cabecalho_participante).json()["id"]
    assert fila.json()["participante_id"] == id_da_fila

    response = client.delete(f"/api/v1/inscricoes/{inscricao_id}", headers=cabecalho)
    assert response.status_code == 204

    inscritos = banco.tabelas["inscricoes"]
    assert len(inscritos) == 1
    assert inscritos[0]["email_participante"] == "b@email.com"
    assert inscritos[0]["usuario_id"] == id_da_fila
    assert banco.tabelas["lista_espera"] == []
