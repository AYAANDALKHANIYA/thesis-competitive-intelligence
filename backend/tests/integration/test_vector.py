import pytest
import math
from app.repositories.analysis import AnalysisRepository
from app.models.company import Company
from app.models.document import Document
from app.models.source import Source

@pytest.mark.asyncio
async def test_vector_insertion(db_session):
    # 1. Create a mock company
    company = Company(name="Test Vector Company", domain="vector.example.com", industry="tech")
    db_session.add(company)
    await db_session.flush()

    # 2. Create a mock source
    source = Source(name="Test Source", source_type="website")
    db_session.add(source)
    await db_session.flush()

    # 3. Create a mock document
    doc = Document(
        company_id=company.id,
        source_id=source.id,
        url="https://vector.example.com/test",
        title="Test Vector",
        content="Test content for vector insertion.",
        content_hash="mockhash",
        document_type="website"
    )
    db_session.add(doc)
    await db_session.flush()

    # 4. Create a 384-dimensional embedding
    repo = AnalysisRepository(db_session)
    embedding = [math.sin(i) for i in range(384)] # Just a dummy list of 384 floats

    # 5. Insert embedding
    emb = await repo.create_embedding(
        document_id=doc.id,
        embedding=embedding,
        model_name="all-MiniLM-L6-v2"
    )
    
    assert emb.id is not None
    assert emb.document_id == doc.id
    
    # 6. Verify we can retrieve it and check dimensions (if applicable)
    has_emb = await repo.has_embedding(doc.id)
    assert has_emb is True
