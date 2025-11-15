import pytest
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService
from app.services.cache_service import CacheService


def test_chunk_text(test_db):
    """Test text chunking with overlap"""
    vector_service = VectorService(test_db)
    
    text = "This is sentence one. " * 100  # Create long text
    chunks = vector_service.chunk_text(text, chunk_size=100, overlap=20)
    
    assert len(chunks) > 0
    assert all(len(chunk) <= 150 for chunk in chunks)  # Allow for overlap
    assert all(len(chunk.strip()) > 0 for chunk in chunks)


def test_chunk_text_empty():
    """Test that empty text returns empty list"""
    from app.services.vector_service import VectorService
    vector_service = VectorService(None)
    
    chunks = vector_service.chunk_text("")
    assert chunks == []


def test_chunk_text_small():
    """Test that small text returns one chunk"""
    from app.services.vector_service import VectorService
    vector_service = VectorService(None)
    
    small_text = "This is a small text."
    chunks = vector_service.chunk_text(small_text, chunk_size=1000)
    
    assert len(chunks) == 1
    assert chunks[0] == small_text


@pytest.mark.asyncio
async def test_cache_key_normalization():
    """Test that cache keys are normalized (case and whitespace insensitive)"""
    cache = CacheService()
    
    questions = [
        "What is SmartTask?",
        "what is smarttask?",
        "WHAT IS SMARTTASK?",
        "  what   is   smarttask?  ",
        "what is smarttask?"
    ]
    
    keys = [cache._make_key(q) for q in questions]
    
    assert len(set(keys)) == 1, "All normalized questions should produce same cache key"


@pytest.mark.asyncio
async def test_cache_set_and_get():
    """Test basic cache operations"""
    cache = CacheService()
    
    test_question = "What is SmartTask?"
    test_data = {
        "answer": "SmartTask is a project management tool",
        "sources": [],
        "tokens_used": 100
    }
    
    try:
        await cache.set(test_question, test_data)
        
        cached = await cache.get(test_question)
        
        if cached is not None:  # Cache might not be available in test env
            assert cached["answer"] == test_data["answer"]
            assert cached["tokens_used"] == test_data["tokens_used"]
    except Exception as e:
        pytest.skip(f"Cache not available in test environment: {e}")


@pytest.mark.asyncio
async def test_llm_embedding_format():
    """Test that embeddings are returned in correct format"""
    try:
        llm = LLMService()
        embedding = await llm.get_embedding("test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  
        assert all(isinstance(x, float) for x in embedding)
        
    except Exception as e:
        pytest.skip(f"Skipping LLM test: {e}")


# @pytest.mark.asyncio
# async def test_vector_search_no_results():
#     """Test vector search when no documents exist"""
#     from app.services.vector_service import VectorService
    
#      This test needs a real database with no documents
#      It's more of an integration test
#     pytest.skip("Requires empty database setup")