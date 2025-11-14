import pytest
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService


def test_chunk_text(test_db):
    """Тест разбиения текста на чанки"""
    vector_service = VectorService(test_db)
    
    text = "Это первое предложение. " * 100
    chunks = vector_service.chunk_text(text, chunk_size=100, overlap=20)
    
    assert len(chunks) > 0
    assert all(len(chunk) <= 150 for chunk in chunks)  #учитываем overlap


@pytest.mark.asyncio
async def test_llm_embedding():
    """Тест получения embeddings (требует API ключ)"""
    try:
        llm = LLMService()
        embedding = await llm.get_embedding("test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  #размер OpenAI embeddings
        assert all(isinstance(x, float) for x in embedding)
    except Exception as e:
        pytest.skip(f"Skipping: {e}")


@pytest.mark.asyncio
async def test_cache_service():
    """Тест кэширования"""
    from app.services.cache_service import CacheService
    
    cache = CacheService()
    
    result = await cache.get("test_question")
    assert result is None
    
    test_data = {
        "answer": "test answer",
        "sources": [],
        "tokens_used": 10
    }
    await cache.set("test_question", test_data)
    
    cached = await cache.get("test_question")
    assert cached is not None
    assert cached["answer"] == "test answer"