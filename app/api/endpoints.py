from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.schemas import (
    QuestionRequest, AnswerResponse, 
    HealthResponse, DocumentUploadResponse
)
from app.services.rag_service import RAGService
from app.services.vector_service import VectorService
from app.services.cache_service import CacheService
from app.database import get_db
from app.models import Document, QueryHistory
from datetime import datetime
from app.utils.logger import logger

router = APIRouter(prefix="/api")


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """Main endpoint for questions - uses RAG pipeline"""
    try:
        rag = RAGService(db)
        answer = await rag.answer_question(request.question)
        return answer
    except Exception as e:
        logger.error(f"Error in /ask: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a new document to the knowledge base"""
    
    if not file.filename.endswith(('.txt', '.md')):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .md files are supported"
        )
    
    try:
        content = await file.read()
        
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 10MB"
            )
        
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File must be valid UTF-8 encoded text"
            )
        
        if len(text_content.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Document content too short (minimum 50 characters)"
            )
        
        vector_service = VectorService(db)
        chunks_count = await vector_service.add_document(file.filename, text_content)
        
        logger.info(f"Successfully uploaded {file.filename}: {chunks_count} chunks")
        
        return DocumentUploadResponse(
            filename=file.filename,
            chunks_created=chunks_count,
            status="success"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint - verifies all services are operational"""
    
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    redis_status = "ok"
    try:
        cache = CacheService()
        redis_ok = await cache.health_check()
        redis_status = "ok" if redis_ok else "error"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "error"
    
    try:
        docs_count = db.query(func.count(Document.id)).scalar()
    except Exception as e:
        logger.error(f"Failed to count documents: {e}")
        docs_count = 0
    
    overall_status = "healthy" if (db_status == "ok" and redis_status == "ok") else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        database=db_status,
        redis=redis_status,
        documents_count=docs_count
    )


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    """Get service usage metrics and statistics"""
    
    try:
        total_queries = db.query(func.count(QueryHistory.id)).scalar()
        
        if total_queries == 0:
            return {
                "total_queries": 0,
                "avg_response_time_seconds": 0,
                "avg_tokens_per_query": 0,
                "total_tokens_used": 0,
                "estimated_cost_usd": 0
            }
        
        stats = db.query(
            func.avg(QueryHistory.response_time).label('avg_time'),
            func.avg(QueryHistory.tokens_used).label('avg_tokens'),
            func.sum(QueryHistory.tokens_used).label('total_tokens')
        ).first()
        
        total_tokens = int(stats.total_tokens or 0)
        estimated_cost = (total_tokens / 1000) * 0.002
        
        return {
            "total_queries": total_queries,
            "avg_response_time_seconds": round(float(stats.avg_time or 0), 3),
            "avg_tokens_per_query": round(float(stats.avg_tokens or 0), 1),
            "total_tokens_used": total_tokens,
            "estimated_cost_usd": round(estimated_cost, 4)
        }
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")