# SmartTask FAQ Service

An intelligent question-answering system based on RAG (Retrieval-Augmented Generation) for SmartTask documentation.

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Configuration](#configuration)
- [Development](#development)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)

## Features

- Semantic search powered by pgvector
- Answer generation via OpenAI GPT-3.5/4
- Redis caching for fast responses
- Automatic document processing on startup
- Usage metrics and monitoring
- Web UI for interaction
- Full test coverage
- Docker Compose deployment

## Architecture
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Browser   │─────▶│   FastAPI    │─────▶│   OpenAI    │
│   /Mobile   │      │   Backend    │      │     API     │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌─────────┐
        │PostgreSQL│  │  Redis   │  │ pgvector│
        │    DB    │  │  Cache   │  │ Search  │
        └──────────┘  └──────────┘  └─────────┘
```

### Technology Stack

- **Backend**: FastAPI 0.121 (Python 3.11)
- **Database**: PostgreSQL 16 + pgvector extension
- **Cache**: Redis 7
- **AI**: OpenAI API (text-embedding-3-small + GPT-3.5/4)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic 2.12
- **Container**: Docker + Docker Compose

## Quick Start

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- 2GB free RAM
- Ports 8000, 5432, 6379 available

### Setup in 3 Steps

**1. Clone the repository**
```bash
git clone https://github.com/Avescodder/SmartTask.git
cd SmartTask
```

**2. Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and set your OpenAI API key:
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

**3. Start the services**
```bash
docker compose up --build
```

Wait approximately 30 seconds for all services to initialize. You should see:
```
smarttask-postgres | database system is ready to accept connections
smarttask-redis    | Ready to accept connections
smarttask-api      | Application startup complete
```

### Access

| Service | URL | Description |
|---|---|---|
| Web UI | http://localhost:8000 | Question interface |
| API Metrics | http://localhost:8000/api/metrics | Usage metrics |
| Health Check | http://localhost:8000/api/health | Service status |

## API Documentation

### POST `/api/ask` — Ask a Question

**Request:**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I create a task in SmartTask?"
  }'
```

**Response:**
```json
{
  "answer": "To create a task in SmartTask, click the '+' button in the top right corner...",
  "sources": [
    {
      "filename": "SmartTask_API.txt",
      "content": "Task creation: POST /api/tasks...",
      "similarity": 0.89
    }
  ],
  "tokens_used": 456,
  "response_time": 2.34,
  "cached": false
}
```

### POST `/api/documents` — Upload a Document
```bash
curl -X POST http://localhost:8000/api/documents \
  -F "file=@my-documentation.txt"
```

**Response:**
```json
{
  "filename": "my-documentation.txt",
  "chunks_created": 5,
  "status": "success"
}
```

### GET `/api/health` — Health Check
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-15T00:16:29.562Z",
  "database": "ok",
  "redis": "ok",
  "documents_count": 2
}
```

### GET `/api/metrics` — Usage Metrics
```bash
curl http://localhost:8000/api/metrics
```

**Response:**
```json
{
  "total_queries": 42,
  "avg_response_time_seconds": 2.15,
  "avg_tokens_per_query": 534.2,
  "total_tokens_used": 22436,
  "estimated_cost_usd": 0.0449
}
```

## Testing

### Run all tests
```bash
docker compose exec api pytest tests/ -v
```

Expected output:
```
===================== 15 passed in 4.47s =====================
```

### Run specific tests
```bash
# API tests only
docker compose exec api pytest tests/test_api.py -v

# RAG tests only
docker compose exec api pytest tests/test_rag.py -v

# With coverage report
docker compose exec api pytest tests/ --cov=app --cov-report=html
```

### RAG Quality Evaluation
```bash
docker compose exec api python -m app.services.eval
```

Sample output:
```
RAG System Evaluation Results
============================================================
Total tests: 8
Passed: 7
Failed: 1
Overall Accuracy: 87.5%
============================================================

Results by Category:
  TASK_MANAGEMENT:
    Passed: 3/4 (75.0%)
  SECURITY:
    Passed: 4/4 (100.0%)
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|---|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key | — | Yes |
| `OPENAI_MODEL` | Generation model | `gpt-3.5-turbo` | No |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` | No |
| `POSTGRES_USER` | Database user | `smarttask` | No |
| `POSTGRES_PASSWORD` | Database password | `password` | No |
| `POSTGRES_DB` | Database name | `smarttask_db` | No |
| `REDIS_HOST` | Redis host | `redis` | No |
| `REDIS_TTL` | Cache TTL (seconds) | `3600` | No |

### RAG Settings

Configure in `app/config.py`:
```python
# Document chunk size
chunk_size: int = 1000

# Overlap between chunks
chunk_overlap: int = 200

# Number of relevant chunks for context
top_k: int = 3
```

### Adding Documents

Documents are automatically loaded from the `documents/` directory on startup:
```bash
# Add a new document
echo "Your documentation content" > documents/new-doc.txt

# Restart the service
docker compose restart api

# Or upload via API
curl -X POST http://localhost:8000/api/documents \
  -F "file=@documents/new-doc.txt"
```

**Document requirements:**
- Format: `.txt` or `.md`
- Encoding: UTF-8
- Minimum size: 50 characters
- Maximum size: 10MB

## Development

### Project Structure
```
smarttask-faq/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Application settings
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── api/
│   │   └── endpoints.py     # API routes
│   ├── services/
│   │   ├── rag_service.py   # RAG pipeline orchestration
│   │   ├── vector_service.py # Vector operations
│   │   ├── llm_service.py   # OpenAI client
│   │   ├── cache_service.py # Redis caching
│   │   └── eval.py          # Quality evaluation
│   └── utils/
│       ├── logger.py        # Logging
│       └── metrics.py       # Performance metrics
├── documents/               # Documents for indexing
├── static/
│   └── index.html           # Web interface
├── tests/                   # Tests
├── docker-compose.yml       # Service orchestration
├── Dockerfile               # Application image
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables
```

### Local Development
```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start only the database and Redis
docker compose up postgres redis

# 4. Set environment variables
export POSTGRES_HOST=localhost
export REDIS_HOST=localhost
export OPENAI_API_KEY=sk-...

# 5. Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Viewing Logs
```bash
# All services
docker compose logs -f

# API only
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api
```

### Database Access
```bash
docker compose exec postgres psql -U smarttask -d smarttask_db

# Useful commands:
\dt                                          # List tables
\d documents                                 # Table structure
SELECT COUNT(*) FROM documents;
SELECT filename, chunk_index FROM documents;
```

## Development Process with Claude

The project was built entirely using Claude (Sonnet 4.5) via the Claude.ai web interface. Below is an overview of the key development stages.

### Stage 1: Planning and Project Structure

Claude assisted with decomposing the requirements into concrete tasks, creating a step-by-step development roadmap, and defining the technology stack. The architecture was designed with clear layer separation: API endpoints, business logic (services), data access (models, database), and utilities (logging, metrics).

### Stage 2: Core Functionality

First iteration covered the foundational RAG pipeline: vector search with pgvector, document chunking with overlap, OpenAI API integration, and basic caching.

### Stage 3: Improvements and Refinements

Based on proactive suggestions from Claude, the following were added: usage metrics and monitoring, improved error handling, optimized LLM prompts, and a RAG evaluation system. Bug fixes included Redis connection issues, vector search errors, and input validation.

### Stage 4: Final Review

All endpoints verified, tests passing, Docker Compose confirmed working, documentation complete, and eval accuracy confirmed above 80%.

### Outcomes

- **Development time**: ~4–5 hours with Claude assistance
- **Lines of code**: ~2000 (including tests and configuration)
- **Test count**: 15 tests
- **RAG quality**: 87.5% accuracy on the evaluation dataset

Without AI assistance, a project of this scope would have taken approximately 2–3 days.

## Performance

### Typical Response Times

| Scenario | Time | Description |
|---|---|---|
| Cache Hit | ~50ms | Response served from Redis |
| Cache Miss (no LLM) | ~1s | Vector search only |
| Cache Miss (full) | ~2–3s | Vector search + answer generation |

### Token Usage

| Operation | Tokens | Approximate Cost |
|---|---|---|
| Embedding (question) | ~20–50 | $0.00001 |
| Embedding (document) | ~500–1000 | $0.0001 |
| LLM generation | ~300–800 | $0.0006–0.0016 |

**Average cost per request:** $0.0017–$0.002

### Optimization Notes

- Caching handles approximately 90% of requests from Redis
- Optimal chunk size is 1000 characters with 200-character overlap
- Top-K=3 balances relevance and response speed
- PostgreSQL connection pool size: 10

## Troubleshooting

### Service fails to start
```bash
docker compose logs api
docker compose logs postgres

docker compose down -v
docker compose up --build
```

### "Module not found" error
```bash
docker compose build --no-cache
docker compose up
```

### Database unavailable
```bash
docker compose ps
docker compose logs postgres

docker compose down -v
docker compose up
```

### OpenAI API errors

**"Invalid API key"** — verify the key in `.env` and confirm it starts with `sk-`.

**"Rate limit exceeded"** — wait a few minutes and check your limits at [platform.openai.com](https://platform.openai.com/account/limits).

**"Insufficient quota"** — add funds to your OpenAI account and check usage on the dashboard.

### Redis unavailable
```bash
docker compose exec redis redis-cli ping
# Expected: PONG

docker compose restart redis
```

### Documents not loading

- Verify file format (`.txt` or `.md` only)
- Confirm UTF-8 encoding
- Check file size (< 10MB)
- Review logs: `docker compose logs api | grep "Loading"`

### Slow responses
```bash
# Check metrics
curl http://localhost:8000/api/metrics

# Clear Redis cache
docker compose exec redis redis-cli FLUSHALL

# Check resource usage
docker stats
```
