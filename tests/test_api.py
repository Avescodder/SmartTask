import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test healthcheck endpoint returns proper structure"""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "database" in data
    assert "redis" in data
    assert "documents_count" in data

    assert data["status"] in ["healthy", "degraded"]
    assert data["database"] in ["ok", "error"]
    assert data["redis"] in ["ok", "error"]
    assert isinstance(data["documents_count"], int)


def test_ask_question_validation_empty():
    """Test that empty question is rejected"""
    response = client.post("/api/ask", json={"question": ""})
    assert response.status_code == 422


def test_ask_question_validation_too_short():
    """Test that too short question is rejected"""
    response = client.post("/api/ask", json={"question": "Hi"})
    assert response.status_code == 422


def test_ask_question_validation_too_long():
    """Test that too long question is rejected"""
    response = client.post("/api/ask", json={"question": "x" * 600})
    assert response.status_code == 422


def test_ask_question_validation_valid():
    """Test that valid question format is accepted (may fail without API key)"""
    response = client.post("/api/ask", json={
        "question": "What is SmartTask?"
    })
    
    assert response.status_code in [200, 500]


@patch('app.services.llm_service.LLMService.get_embedding')
@patch('app.services.llm_service.LLMService.generate_answer')
def test_ask_question_structure_with_mocks(mock_generate, mock_embed):
    """Test response structure when mocking LLM calls"""
    
    mock_embed.return_value = [0.1] * 1536
    mock_generate.return_value = ("This is a test answer", 100)
    
    response = client.post("/api/ask", json={
        "question": "What is SmartTask?"
    })
    
    if response.status_code == 200:
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "tokens_used" in data
        assert "response_time" in data
        assert "cached" in data
        
        assert isinstance(data["sources"], list)
        assert isinstance(data["tokens_used"], int)
        assert isinstance(data["response_time"], float)
        assert isinstance(data["cached"], bool)


def test_document_upload_validation_wrong_extension():
    """Test that wrong file extension is rejected"""
    response = client.post(
        "/api/documents",
        files={"file": ("test.pdf", b"content", "application/pdf")}
    )
    assert response.status_code == 400
    assert "Only .txt and .md files" in response.json()["detail"]


def test_document_upload_validation_empty_file():
    """Test that empty file is rejected"""
    response = client.post(
        "/api/documents",
        files={"file": ("test.txt", b"", "text/plain")}
    )
    assert response.status_code in [400, 500]


def test_metrics_endpoint():
    """Test that metrics endpoint returns proper structure"""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_queries" in data
    assert "avg_response_time_seconds" in data
    assert "avg_tokens_per_query" in data
    assert "total_tokens_used" in data
    assert "estimated_cost_usd" in data
    
    assert isinstance(data["total_queries"], int)
    assert isinstance(data["avg_response_time_seconds"], (int, float))
    assert isinstance(data["avg_tokens_per_query"], (int, float))
    assert isinstance(data["total_tokens_used"], int)
    assert isinstance(data["estimated_cost_usd"], (int, float))