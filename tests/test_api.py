from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Тест healthcheck endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "database" in data


def test_ask_question_validation():
    """Тест валидации входных данных"""
    response = client.post("/api/ask", json={"question": ""})
    assert response.status_code == 422
    
    response = client.post("/api/ask", json={"question": "Hi"})
    assert response.status_code == 422
    
    response = client.post("/api/ask", json={"question": "Как создать задачу?"})
    assert response.status_code in [200, 500]  


def test_ask_question_structure():
    """Тест структуры ответа (если есть API ключ)"""
    response = client.post("/api/ask", json={
        "question": "Что такое SmartTask?"
    })
    
    if response.status_code == 200:
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "tokens_used" in data
        assert "response_time" in data
        assert isinstance(data["sources"], list)


def test_document_upload_validation():
    """Тест валидации загрузки документов"""
    response = client.post(
        "/api/documents",
        files={"file": ("test.pdf", b"content", "application/pdf")}
    )
    assert response.status_code == 400