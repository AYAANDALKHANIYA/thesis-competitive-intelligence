import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch
import hashlib
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# SQLite type mappings
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "testing"

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw): return "JSON"

from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
@compiles(PG_ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw): return "TEXT"

try:
    from pgvector.sqlalchemy import Vector
    @compiles(Vector, "sqlite")
    def compile_vector_sqlite(type_, compiler, **kw): return "TEXT"
except ImportError:
    pass

from app.db.base import Base
from app.models.document import Document
from app.models.company import Company
from app.models.source import Source
from app.models.analysis import AnalysisRun, AnalysisCompetitor
from app.services.llm.evidence_builder import EvidenceBuilder
from app.services.llm.insight_generator import InsightGenerator

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        # Avoid index errors on sqlite for postgresql_where
        for table in Base.metadata.tables.values():
            for index in list(table.indexes):
                if index.name == "ix_companies_is_primary":
                    table.indexes.remove(index)
        await conn.run_sync(Base.metadata.create_all)
        
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
    
    await engine.dispose()

@pytest_asyncio.fixture
async def sample_company(db_session):
    company = Company(name="Test Co", domain="testco.com", is_primary=True)
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company

@pytest_asyncio.fixture
async def sample_source(db_session):
    source = Source(name="Test Source", source_type="website")
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source

@pytest.mark.asyncio
async def test_duplicate_url_and_changed_content(db_session, sample_company, sample_source):
    initial_content = "This is some content."
    initial_hash = hashlib.sha256(initial_content.encode('utf-8')).hexdigest()
    
    doc1 = Document(
        company_id=sample_company.id,
        source_id=sample_source.id,
        url="https://testco.com/page",
        title="Page 1",
        content=initial_content,
        content_hash=initial_hash,
        document_type="web_page",
        is_processed=True
    )
    db_session.add(doc1)
    await db_session.commit()
    await db_session.refresh(doc1)

    class DummyResult:
        def __init__(self, url, title, content, document_type, metadata=None):
            self.url = url
            self.title = title
            self.content = content
            self.document_type = document_type
            self.metadata = metadata or {}

    async def mock_save(results, s_id, comp_id, session):
        docs = []
        for r in results:
            url = r.url[:2000]
            content = r.content or ""
            c_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            existing_result = await session.execute(
                select(Document).where(Document.company_id == comp_id, Document.url == url)
            )
            existing_doc = existing_result.scalars().first()
            
            if existing_doc:
                if existing_doc.content_hash == c_hash:
                    docs.append(existing_doc)
                    continue
                else:
                    existing_doc.content = content
                    existing_doc.content_hash = c_hash
                    existing_doc.is_processed = False
                    docs.append(existing_doc)
                    continue
            
            new_doc = Document(
                company_id=comp_id,
                source_id=s_id,
                url=url,
                title=r.title[:500] if r.title else None,
                content=content,
                content_hash=c_hash,
                document_type=r.document_type,
                metadata_=r.metadata
            )
            session.add(new_doc)
            docs.append(new_doc)
        await session.flush()
        return docs

    # Exact duplicate test
    results = [DummyResult("https://testco.com/page", "Page 1", initial_content, "web_page")]
    saved_docs = await mock_save(results, sample_source.id, sample_company.id, db_session)
    await db_session.commit()
    
    assert len(saved_docs) == 1
    assert saved_docs[0].id == doc1.id
    assert saved_docs[0].is_processed == True 

    # Changed content test
    new_content = "This is completely new content."
    results2 = [DummyResult("https://testco.com/page", "Page 1 Updated", new_content, "web_page")]
    saved_docs2 = await mock_save(results2, sample_source.id, sample_company.id, db_session)
    await db_session.commit()
    
    assert len(saved_docs2) == 1
    assert saved_docs2[0].id == doc1.id
    assert saved_docs2[0].content == new_content
    assert saved_docs2[0].is_processed == False 

@pytest.mark.asyncio
async def test_evidence_normalization_and_missing_dates(db_session, sample_company, sample_source):
    doc = Document(
        company_id=sample_company.id,
        source_id=sample_source.id,
        url="https://testco.com/missing-date",
        title=None,
        content="Short text",
        content_hash="abc",
        document_type=None,
        collected_at=None
    )
    db_session.add(doc)
    await db_session.commit()

    builder = EvidenceBuilder(db_session)
    evidence = await builder._document_evidence(sample_company.id)
    
    assert len(evidence) == 1
    assert evidence[0]["company"] == sample_company.name
    assert evidence[0]["title"] == "Untitled"
    assert evidence[0]["publication_date"] == "Unknown"
    assert evidence[0]["evidence_type"] == "web_page"
    assert evidence[0]["text_excerpt"] == "Short text"

@pytest.mark.asyncio
async def test_malformed_llm_json(db_session, sample_company):
    generator = InsightGenerator()
    parsed = generator._parse_response("Not a JSON object")
    
    assert parsed["title"] == "Market Intelligence Insight"
    assert parsed["summary"] == "Not a JSON object"
    assert parsed["severity"] == "medium"

@pytest.mark.asyncio
@patch("app.db.session.async_session_factory")
async def test_llm_unavailable(mock_session_factory, db_session, sample_company, monkeypatch):
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def mock_factory():
        yield db_session
    mock_session_factory.side_effect = mock_factory

    generator = InsightGenerator()
    
    async def mock_call(*args, **kwargs):
        return None
    
    monkeypatch.setattr(generator, "_call_llm", mock_call)
    
    insight = await generator.generate_insight(sample_company.id, sample_company.name, force=True)
    
    assert "error" in insight
    assert insight["error"] == "LLM call failed"
