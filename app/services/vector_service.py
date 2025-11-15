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
        """Split text into overlapping chunks for better context preservation"""
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
            
            chunk_stripped = chunk.strip()
            if chunk_stripped:  
                chunks.append(chunk_stripped)
            
            start = end - overlap
        
        return chunks
    
    async def add_document(self, filename: str, content: str) -> int:
        """Add document to vector database with embeddings"""
        
        chunks = self.chunk_text(content)
        logger.info(f"Created {len(chunks)} chunks for {filename}")
        
        if not chunks:
            raise ValueError("Document produced no valid chunks")
        
        for i, chunk in enumerate(chunks):
            try:
                embedding = await self.llm.get_embedding(chunk)
                
                doc = Document(
                    filename=filename,
                    content=chunk,
                    chunk_index=i,
                    embedding=embedding  
                )
                self.db.add(doc)
                
            except Exception as e:
                logger.error(f"Error processing chunk {i} of {filename}: {e}")
                raise
        
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit document {filename}: {e}")
            raise
        
        return len(chunks)
    
    async def search_similar(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """Search for similar document chunks using cosine similarity"""
        
        try:
            query_embedding = await self.llm.get_embedding(query)
            
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            sql = text("""
                SELECT 
                    filename, 
                    content, 
                    1 - (embedding <=> :embedding::vector) as similarity
                FROM documents
                ORDER BY embedding <=> :embedding::vector
                LIMIT :limit
            """)
            
            result = self.db.execute(
                sql,
                {"embedding": embedding_str, "limit": top_k}
            )
            
            similar_docs = [
                (row.filename, row.content, float(row.similarity)) 
                for row in result
            ]
            
            if not similar_docs:
                logger.warning(f"No similar documents found for query: {query[:50]}...")
            else:
                logger.info(f"Found {len(similar_docs)} similar documents")
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}", exc_info=True)
            raise