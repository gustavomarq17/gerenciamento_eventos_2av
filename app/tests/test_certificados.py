from uuid import UUID


def criar_inscricao(banco, status="ATIVA", presente=False):
    banco.tabelas.setdefault("inscricoes", []).append({
        "id": 1, "created_at": "2026-01-01T00:00:00+00:00", "nome_participante": "Ana",
        "email_participante": "ana@teste.com", "evento_id": 1, "status": status, "presente": presente,
    })


def test_rotas_de_certificados_sem_token_retornam_401(client):
    assert client.post("/api/v1/certificados/", json={"inscricao_id": 1}).status_code == 401
    assert client.get("/api/v1/certificados/").status_code == 401
    assert client.get("/api/v1/certificados/4b8f2a8e-3c1d-4e5f-9a7b-1c2d3e4f5a6b").status_code == 401
    assert client.delete("/api/v1/certificados/1").status_code == 401


def test_emitir_sem_presenca_retorna_400(client, banco, cabecalho_admin):
    criar_inscricao(banco, presente=False)
    resposta = client.post("/api/v1/certificados/", json={"inscricao_id": 1}, headers=cabecalho_admin)
    assert resposta.status_code == 400
    assert "presença" in resposta.json()["detail"]


def test_emitir_para_inscricao_cancelada_retorna_400(client, banco, cabecalho_admin):
    criar_inscricao(banco, status="CANCELADA", presente=True)
    resposta = client.post("/api/v1/certificados/", json={"inscricao_id": 1}, headers=cabecalho_admin)
    assert resposta.status_code == 400


def test_emitir_para_inscricao_inexistente_retorna_404(client, cabecalho_admin):
    resposta = client.post("/api/v1/certificados/", json={"inscricao_id": 999}, headers=cabecalho_admin)
    assert resposta.status_code == 404


def test_fluxo_completo_do_certificado(client, banco, cabecalho_admin):
    criar_inscricao(banco)

    presenca = client.patch("/api/v1/inscricoes/1/presenca", headers=cabecalho_admin)
    assert presenca.json()["presente"] is True

    emitido = client.post("/api/v1/certificados/", json={"inscricao_id": 1}, headers=cabecalho_admin)
    assert emitido.status_code == 201
    certificado = emitido.json()
    UUID(certificado["codigo_validador"])

    repetido = client.post("/api/v1/certificados/", json={"inscricao_id": 1}, headers=cabecalho_admin)
    assert repetido.status_code == 400

    assert len(client.get("/api/v1/certificados/", headers=cabecalho_admin).json()) == 1
    validado = client.get(f"/api/v1/certificados/{certificado['codigo_validador']}", headers=cabecalho_admin)
    assert validado.status_code == 200
    assert validado.json()["inscricao_id"] == 1

    assert client.put(f"/api/v1/certificados/{certificado['id']}", json={"codigo_validador": "x"}, headers=cabecalho_admin).status_code == 405

    assert client.delete(f"/api/v1/certificados/{certificado['id']}", headers=cabecalho_admin).status_code == 204
    assert client.get(f"/api/v1/certificados/{certificado['codigo_validador']}", headers=cabecalho_admin).status_code == 404
    assert client.delete(f"/api/v1/certificados/{certificado['id']}", headers=cabecalho_admin).status_code == 404


def test_codigo_malformado_retorna_422_e_inexistente_404(client, cabecalho):
    assert client.get("/api/v1/certificados/codigo-invalido", headers=cabecalho).status_code == 422
    assert client.get("/api/v1/certificados/4b8f2a8e-3c1d-4e5f-9a7b-1c2d3e4f5a6b", headers=cabecalho).status_code == 404
