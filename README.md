# Sanad AEO Auditor

Answer Engine Optimization (AEO) auditor for Arabic e-commerce sites.

## Features

- ✅ **Protocol Compliance**: Check llms.txt, agent-card.json, robots.txt
- ✅ **Edge Visibility**: Test AI agent access (Cloudflare, CDN blocking)
- ✅ **Schema Validation**: Validate Product JSON-LD structured data
- ✅ **Content Quality**: Score Arabic content using local Ollama LLM
- ✅ **Bilingual Check**: Verify Arabic/English hreflang symmetry
- ✅ **Comprehensive Reports**: Severity-based issue prioritization

## Tech Stack

- **Backend**: FastAPI (async)
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL
- **Crawler**: Crawl4AI
- **LLM**: Ollama (qwen3:8b)
- **Storage**: Local filesystem

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose

### Setup

1. **Clone and navigate to project**
   ```bash
   cd SanadChecker
   ```

2. **Create environment file**
   ```bash
   copy .env.example .env
   ```

3. **Start services with Docker**
   ```bash
   docker-compose up -d postgres redis ollama
   ```

4. **Pull Ollama model**
   ```bash
   docker exec -it sanadchecker-ollama-1 ollama pull qwen2.5:7b
   ```

5. **Install Python dependencies**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

6. **Initialize database**
   ```bash
   # Create tables (Alembic migrations coming soon)
   python -c "from app.database import engine; from app.models.audit import Base; Base.metadata.create_all(engine)"
   ```

7. **Start FastAPI server**
   ```bash
   uvicorn app.main:app --reload
   ```

8. **Start Celery worker** (in new terminal)
   ```bash
   venv\Scripts\activate
   celery -A app.celery_app worker --loglevel=info --pool=solo
   ```

### Using the API

**Submit an audit:**
```bash
curl -X POST http://localhost:8000/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{"url": "https://store.salla.sa/product/123"}'
```

**Check audit status:**
```bash
curl http://localhost:8000/api/v1/audits/{audit_id}
```

**Get report:**
```bash
curl http://localhost:8000/api/v1/audits/{audit_id}/report
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
SanadChecker/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic (TODO)
│   ├── tasks/           # Celery tasks
│   ├── config.py        # Configuration
│   ├── database.py      # Database connection
│   ├── main.py          # FastAPI app
│   └── celery_app.py    # Celery configuration
├── .agent/skills/       # AI agent skills
├── docker-compose.yml   # Docker services
├── Dockerfile          # Container image
├── requirements.txt     # Python dependencies
└── .env.example        # Environment template
```

## Development Roadmap

### Phase 1: Core Infrastructure ✅
- [x] FastAPI project structure
- [x] Database models
- [x] API endpoints
- [x] Celery task queue
- [x] Docker setup

### Phase 2: Service Implementation (In Progress)
- [ ] Crawl4AI page extraction
- [ ] Protocol checker (llms.txt, A2A, robots.txt)
- [ ] Edge visibility tester
- [ ] JSON-LD schema validator
- [ ] Ollama content scorer
- [ ] Report generator

### Phase 3: Polish
- [ ] Alembic database migrations
- [ ] Unit tests
- [ ] Integration tests
- [ ] API rate limiting
- [ ] Error handling improvements

### Phase 4: Frontend (Optional)
- [ ] React dashboard
- [ ] Audit visualization
- [ ] Real-time progress tracking

## Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Celery workers
curl http://localhost:8000/health/celery
```

## Skills

The `.agent/skills/` directory contains specialized AI skills for AEO auditing:

- **aeo-protocol-checker**: Validate protocol files
- **arabic-normalizer**: Arabic text processing
- **jsonld-validator**: Schema validation
- **human-first-scorer**: Content quality analysis
- **crawl4ai-extractor**: Page extraction
- **edge-visibility-tester**: AI agent blocking detection
- **audit-reporter**: Report generation
- **frontend-design**: UI/UX guidelines

## License

Proprietary - Sanad Project
