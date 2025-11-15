import time
from sqlalchemy.orm import Session
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService
from app.services.cache_service import CacheService
from app.schemas import AnswerResponse, Source
from app.models import QueryHistory
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()
        self.vector = VectorService(db)
        self.cache = CacheService()
    
    async def answer_question(self, question: str) -> AnswerResponse:
        """Главный метод RAG pipeline"""
        start_time = time.time()
        
        cached = await self.cache.get(question)
        if cached:
            cached['cached'] = True
            cached['response_time'] = time.time() - start_time
            return AnswerResponse(**cached)
        
        similar_docs = await self.vector.search_similar(question, settings.top_k)
        
        if not similar_docs:
            return AnswerResponse(
                answer="К сожалению, я не нашёл информации по вашему вопросу.",
                sources=[],
                tokens_used=0,
                response_time=time.time() - start_time
            )
        
        context = "\n\n".join([
            f"[{doc[0]}]\n{doc[1]}" for doc in similar_docs
        ])
        
        answer, tokens = await self.llm.generate_answer(question, context)
        
        sources = [
            Source(
                filename=doc[0],
                content=doc[1][:200] + "...",
                similarity=round(doc[2], 3)
            )
            for doc in similar_docs
        ]
        
        response_time = time.time() - start_time
        
        history = QueryHistory(
            question=question,
            answer=answer,
            sources=str([s.filename for s in sources]),
            tokens_used=tokens,
            response_time=response_time
        )
        self.db.add(history)
        self.db.commit()
        
        response_data = {
            "answer": answer,
            "sources": [s.model_dump() for s in sources],
            "tokens_used": tokens,
            "response_time": response_time
        }
        await self.cache.set(question, response_data)
        
        logger.info(f"RAG pipeline completed in {response_time:.2f}s")
        
        return AnswerResponse(**response_data)