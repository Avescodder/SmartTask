from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.schemas import (
    QuestionRequest, AnswerResponse, 
    HealthResponse, DocumentUploadResponse
)
from app.services.rag_service import RAGService
from app.services.vector_service import VectorService
from app.services.cache_service import CacheService
from app.database import get_db
from app.models import Document
from datetime import datetime
from app.utils.logger import logger

router = APIRouter(prefix="/api")


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """Основной endpoint для вопросов"""
    try:
        with get_db() as db:
            rag = RAGService(db)
            answer = await rag.answer_question(request.question)
            return answer
    except Exception as e:
        logger.error(f"Error in /ask: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Загрузка нового документа в базу знаний"""
    if not file.filename.endswith(('.txt', '.md')):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .md files are supported"
        )
    
    try:
        content = await file.read()
        text = content.decode('utf-8')
        
        with get_db() as db:
            vector_service = VectorService(db)
            chunks_count = await vector_service.add_document(file.filename, text)
        
        logger.info(f"Uploaded {file.filename}: {chunks_count} chunks")
        
        return DocumentUploadResponse(
            filename=file.filename,
            chunks_created=chunks_count,
            status="success"
        )
    
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Healthcheck endpoint"""
    from app.database import engine
    
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "ok"
    except:
        db_status = "error"
    
    cache = CacheService()
    redis_ok = await cache.health_check()
    redis_status = "ok" if redis_ok else "error"
    
    with get_db() as db:
        docs_count = db.query(Document).count()
    
    return HealthResponse(
        status="healthy" if db_status == "ok" and redis_status == "ok" else "degraded",
        timestamp=datetime.now(),
        database=db_status,
        redis=redis_status,
        documents_count=docs_count
    )