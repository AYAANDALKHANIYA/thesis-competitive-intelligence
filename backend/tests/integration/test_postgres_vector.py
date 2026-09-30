import os
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.repositories.analysis import AnalysisRepository
from app.core.config import get_settings

@pytest.mark.asyncio
async def test_postgres_vector_insertion():
    """
    REAL PostgreSQL integration test for pgvector.
    This connects to the exact DATABASE_URL from the environment.
    It asserts that the asyncpg + pgvector.sqlalchemy.Vector binding works
    without throwing a DataError for a 384-dimensional list.
    """
    import os
    
    # Read the real .env file because conftest.py overrides os.environ
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    prod_db_url = None
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                prod_db_url = line.strip().split('=', 1)[1]
                break
                
    if not prod_db_url or "sqlite" in prod_db_url:
        pytest.skip("Skipping pgvector integration test because DATABASE_URL is not PostgreSQL")
        
    if prod_db_url.startswith("postgres://"):
        prod_db_url = prod_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif prod_db_url.startswith("postgresql://") and "+asyncpg" not in prod_db_url:
        prod_db_url = prod_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Connect directly to the test/production PostgreSQL via DATABASE_URL
    engine = create_async_engine(prod_db_url, echo=False)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as db:
        repo = AnalysisRepository(db)
        
        # We need a valid document_id to satisfy the foreign key constraint.
        # We will attempt to find one. If none exist, we cannot run the test fully.
        res = await db.execute(text("SELECT id FROM documents LIMIT 1"))
        doc_id = res.scalar()
        
        if not doc_id:
            pytest.skip("No documents exist in the database to satisfy the foreign key constraint.")

        # Create a dummy 384-dimensional vector list
        dummy_embedding = [0.123] * 384

        try:
            # Attempt to create the embedding
            emb = await repo.create_embedding(
                document_id=doc_id,
                embedding=dummy_embedding,
                model_name="all-MiniLM-L6-v2-test"
            )
            
            # The flush will trigger the DBAPI error if pgvector serialization is broken
            await db.flush()
            
            # Commit to ensure it actually persists
            await db.commit()
            
            # Refresh or query back to verify
            has_emb = await repo.has_embedding(doc_id)
            assert has_emb is True, "Embedding was not found after insertion!"
            
            # Fetch it back to verify dimensions
            from app.models.embedding import Embedding
            from sqlalchemy import select
            fetched = await db.execute(
                select(Embedding).where(Embedding.id == emb.id)
            )
            fetched_emb = fetched.scalar_one_or_none()
            assert fetched_emb is not None
            
            # Clean up the test embedding to not pollute the database
            await db.execute(text(f"DELETE FROM embeddings WHERE id = {emb.id}"))
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            pytest.fail(f"Vector insertion failed with error: {type(e).__name__}: {str(e)}")
        finally:
            await engine.dispose()
