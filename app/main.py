from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.endpoints import router
from app.database import init_db, get_db
from app.services.vector_service import VectorService
from app.utils.logger import logger
from app.config import get_settings
from pathlib import Path

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup и shutdown события"""
    logger.info("Starting SmartTask FAQ Service...")
    
    init_db()
    logger.info("Database initialized")
    
    await load_initial_documents()
    
    yield
    
    logger.info("Shutting down...")


async def load_initial_documents():
    """Загружаем документы из папки documents/ при старте"""
    docs_path = Path("documents")
    
    if not docs_path.exists():
        logger.warning("Documents folder not found")
        return
    
    with get_db() as db:
        from app.models import Document
        if db.query(Document).count() > 0:
            logger.info("Documents already loaded, skipping")
            return
        
        vector_service = VectorService(db)
        
        for file_path in docs_path.glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                chunks = await vector_service.add_document(
                    file_path.name,
                    content
                )
                logger.info(f"Loaded {file_path.name}: {chunks} chunks")
            
            except Exception as e:
                logger.error(f"Error loading {file_path.name}: {e}")

app = FastAPI(
    title="SmartTask FAQ Service",
    description="RAG-based Q&A system for SmartTask documentation",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )