from fastapi.testclient import TestClient
from unittest.mock import patch
# Ajuste o import do app conforme a estrutura principal do seu projeto (ex: from main import app ou from app.main import app)
from main import app 

client = TestClient(app)

@patch("app.routers.inscricoes.supabase")
def test_realizar_inscricao_evento_inativo(mock_supabase):
    # Simulando que o evento buscado está com status INATIVO ou cancelado
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": 1, "titulo": "Palestra Teste", "status": "INATIVO", "capacidade": 50}
    ]

    payload = {
        "participante_id": 1,
        "evento_id": 1,
        "email_participante": "teste@email.com"
    }

    response = client.post("/inscricoes/", json=payload)

    # O código deve barrar e retornar erro 400 informando que o evento é inativo
    assert response.status_code == 400
    assert "Não é possível se inscrever em eventos inativos" in response.json()["detail"]