# AI-Powered Competitive Intelligence & Market Trend Prediction Platform

A full-stack backend API for real-time competitive intelligence gathering, NLP analysis, and market trend prediction. Built with **FastAPI**, **PostgreSQL** (with **pgvector**), transformer-based NLP, and ML prediction models.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Data Pipeline](#data-pipeline)
- [Testing](#testing)
- [Deployment (Railway)](#deployment-railway)

---

## Architecture Overview

```
FastAPI REST API
    ├── Service Layer
    │   ├── Ingestion Orchestrator → Source Adapters (Website, RSS, GDELT, SEC EDGAR)
    │   ├── Processing Pipeline (Cleaner → Normaliser → Deduplicator)
    │   ├── NLP Pipeline (Sentiment, Topics, Entities, Embeddings)
    │   ├── Intelligence Engine (Competitor Metrics, Trends, Emerging Signals, MAI)
    │   ├── Prediction Engine (Feature Engineering → XGBoost / Prophet → Evaluator)
    │   └── LLM Insight Generator (Evidence Builder → OpenAI)
    ├── Repositories (async SQLAlchemy CRUD)
    └── PostgreSQL + pgvector
```

---

## Features

- **Multi-source data ingestion**: Website scraping, RSS/Atom feeds, GDELT news, SEC EDGAR filings
- **Smart fetching**: ETag/Last-Modified caching, content hashing, deduplication, rate limiting
- **NLP pipeline**: Transformer-based sentiment (3-class), BERTopic topic modelling, spaCy NER, sentence embeddings
- **Competitive intelligence**: Competitor activity scoring, topic momentum, emerging signal detection
- **Market Activity Index**: Configurable weighted composite index
- **Prediction engine**: XGBoost regression, Prophet forecasting, model versioning & evaluation
- **LLM insights**: Evidence-grounded insight generation via OpenAI (GPT-4o-mini)
- **Background scheduling**: APScheduler for automated ingestion and analysis
- **Full REST API**: 40+ endpoints with Pydantic validation, pagination, filtering

---

## Technology Stack

| Category | Packages |
|---|---|
| **Web** | FastAPI, Uvicorn, Pydantic v2, pydantic-settings |
| **Database** | SQLAlchemy 2.x (async), asyncpg, Alembic, pgvector |
| **HTTP** | httpx, tenacity (retry) |
| **Scraping** | BeautifulSoup4, lxml, feedparser |
| **NLP** | Transformers, Sentence Transformers, BERTopic, spaCy |
| **ML** | XGBoost, Prophet, pandas, numpy, scikit-learn |
| **Scheduling** | APScheduler |
| **LLM** | OpenAI Python SDK |
| **Testing** | pytest, pytest-asyncio, pytest-cov, aiosqlite |

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with [pgvector](https://github.com/pgvector/pgvector) extension
- (Optional) spaCy model: `python -m spacy download en_core_web_sm`

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set up environment
cp .env.example .env
# Edit .env with your database URL, API keys, etc.
```

### Database Setup

```bash
# Enable pgvector extension (in psql)
CREATE EXTENSION IF NOT EXISTS vector;

# Run migrations
alembic upgrade head
```

### Seed Data (Optional)

```bash
# Seed default data sources
python scripts/seed_sources.py

# Seed demo companies (Microsoft, Apple, Google)
python scripts/seed_demo_companies.py
```

### Run the Server

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `OPENAI_API_KEY` | OpenAI API key for LLM insights | — |
| `ENVIRONMENT` | `development` / `production` | `development` |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` | `INFO` |
| `USER_AGENT` | HTTP User-Agent for web requests | `CompetitiveIntelPlatform/1.0` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000,...` |
| `API_KEY` | Optional API key for authentication | — |
| `SENTIMENT_MODEL` | HuggingFace model name | `cardiffnlp/twitter-roberta-base-sentiment-latest` |
| `EMBEDDING_MODEL` | Sentence Transformers model | `all-MiniLM-L6-v2` |
| `SPACY_MODEL` | spaCy model name | `en_core_web_sm` |
| `NLP_BATCH_SIZE` | Batch size for NLP processing | `32` |

See [`.env.example`](.env.example) for the full list of configurable variables.

---

## API Reference

### Health

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness check |
| `/health/db` | GET | Database connectivity |
| `/health/sources` | GET | Source adapter status |

### Companies

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/companies` | GET | List companies (paginated) |
| `/api/v1/companies` | POST | Create company |
| `/api/v1/companies/{id}` | GET | Get company details |
| `/api/v1/companies/{id}` | PATCH | Update company |
| `/api/v1/companies/{id}` | DELETE | Delete company |

### Sources

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/sources` | GET | List data sources |
| `/api/v1/sources/{id}` | PATCH | Update source config |

### Competitors

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/companies/{id}/competitors` | GET | List competitors |
| `/api/v1/companies/{id}/competitors` | POST | Add competitor |
| `/api/v1/companies/{id}/competitors/{cid}` | DELETE | Remove competitor |

### Documents

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/documents` | GET | List documents (filtered) |
| `/api/v1/documents/{id}` | GET | Get document detail |

### Analytics

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/analytics/sentiment` | GET | Sentiment analysis results |
| `/api/v1/analytics/topics` | GET | Topic distribution |
| `/api/v1/analytics/entities` | GET | Named entity listing |
| `/api/v1/analytics/trends` | GET | Topic trends |
| `/api/v1/analytics/signals` | GET | Emerging signals |

### Predictions

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/predictions` | GET | List predictions |
| `/api/v1/predictions/generate` | POST | Generate predictions |
| `/api/v1/predictions/models` | GET | Model performance |

### Insights

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/insights` | GET | List insights |
| `/api/v1/insights/generate` | POST | Generate LLM insights |

### Ingestion

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/ingestion/trigger` | POST | Trigger ingestion |
| `/api/v1/ingestion/status` | GET | Ingestion run status |

### System

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/system/stats` | GET | Platform statistics |
| `/api/v1/system/sources/health` | GET | Source health status |

---

## Project Structure

```
backend/
├── alembic.ini                 # Alembic migration config
├── requirements.txt            # Python dependencies
├── Procfile                    # Railway start command
├── railway.toml                # Railway build config
├── .env.example                # Environment variable template
├── app/
│   ├── main.py                 # FastAPI app factory
│   ├── core/
│   │   ├── config.py           # Pydantic settings
│   │   ├── logging.py          # Structured logging (structlog)
│   │   ├── security.py         # API key validation
│   │   └── rate_limit.py       # Token-bucket rate limiter
│   ├── db/
│   │   ├── base.py             # Declarative base + mixins
│   │   ├── session.py          # Async engine + session factory
│   │   └── migrations/         # Alembic migrations
│   ├── models/                 # SQLAlchemy ORM models (15 tables)
│   ├── schemas/                # Pydantic request/response schemas
│   ├── repositories/           # Database CRUD operations
│   ├── services/
│   │   ├── extraction/         # Source adapters (website, rss, gdelt, sec)
│   │   ├── ingestion/          # Orchestrator, scheduler, policies
│   │   ├── processing/         # Cleaner, normaliser, deduplicator
│   │   ├── nlp/                # Sentiment, topics, entities, embeddings
│   │   ├── intelligence/       # Competitor, trends, signals, MAI
│   │   ├── prediction/         # Features, XGBoost, Prophet, evaluator
│   │   └── llm/                # Evidence builder, insight generator
│   ├── api/routes/             # API endpoint handlers
│   └── tasks/                  # Background task orchestration
├── scripts/                    # Seed data and manual runners
└── tests/
    ├── conftest.py             # Test fixtures (SQLite-backed)
    ├── unit/                   # Pure-logic unit tests
    └── integration/            # API endpoint integration tests
```

---

## Data Pipeline

The platform operates a multi-stage data pipeline:

1. **Ingestion**: Source adapters fetch data from websites, RSS feeds, GDELT, and SEC EDGAR
2. **Processing**: HTML cleaning, text normalisation, near-duplicate detection
3. **NLP Analysis**: Sentiment scoring, topic assignment, entity extraction, embedding generation
4. **Intelligence**: Competitor metrics, trend analysis, emerging signal detection, MAI calculation
5. **Prediction**: Feature engineering → XGBoost/Prophet → evaluation → model registry
6. **Insights**: LLM-powered insight generation with evidence grounding

The pipeline can be triggered:
- **Manually**: `POST /api/v1/ingestion/trigger` or `python scripts/run_ingestion.py`
- **Automatically**: APScheduler runs on configurable intervals in production

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

Tests use SQLite (via aiosqlite) for the database layer, so no PostgreSQL is needed for testing.

---

## Deployment (Railway)

### Quick Deploy

1. Push to GitHub
2. Create a new Railway project
3. Add a **PostgreSQL** plugin and enable the `vector` extension
4. Connect your repository
5. Set environment variables in Railway dashboard
6. Deploy

### Required Railway Environment Variables

```
DATABASE_URL=<auto-set by Railway PostgreSQL plugin>
OPENAI_API_KEY=<your key>
ENVIRONMENT=production
USER_AGENT=CompetitiveIntelPlatform/1.0 (your-email@example.com)
```

### Post-Deploy

```bash
# Run migrations (via Railway CLI or shell)
alembic upgrade head

# Seed initial data
python scripts/seed_sources.py
python scripts/seed_demo_companies.py
```

---

## License

This project is for academic and research purposes.
