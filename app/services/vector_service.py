from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Tuple
from app.models import Document
from app.services.llm_service import LLMService
from app.utils.logger import logger


class VectorService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Разбиваем текст на чанки с перекрытием"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                split_point = max(last_period, last_newline)
                
                if split_point > chunk_size * 0.5:
                    chunk = chunk[:split_point + 1]
                    end = start + split_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    async def add_document(self, filename: str, content: str) -> int:
        """Добавляем документ в векторную БД"""
        chunks = self.chunk_text(content)
        logger.info(f"Created {len(chunks)} chunks for {filename}")
        
        for i, chunk in enumerate(chunks):
            embedding = await self.llm.get_embedding(chunk)
            
            doc = Document(
                filename=filename,
                content=chunk,
                chunk_index=i,
                embedding=embedding
            )
            self.db.add(doc)
        
        self.db.commit()
        return len(chunks)
    
    async def search_similar(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """Ищем похожие документы используя cosine similarity"""
        query_embedding = await self.llm.get_embedding(query)
        
        sql = text("""
            SELECT filename, content, 1 - (embedding <=> :embedding) as similarity
            FROM documents
            ORDER BY embedding <=> :embedding
            LIMIT :limit
        """)
        
        result = self.db.execute(
            sql,
            {"embedding": str(query_embedding), "limit": top_k}
        )
        
        similar_docs = [(row.filename, row.content, row.similarity) for row in result]
        logger.info(f"Found {len(similar_docs)} similar documents")
        
        return similar_docs