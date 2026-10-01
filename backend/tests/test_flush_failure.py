import datetime
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.company import Company
from app.models.metric import MarketMetric
from app.db.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("DROP TABLE market_metrics"))
        await conn.execute(text("""
            CREATE TABLE market_metrics (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                analysis_id INTEGER,
                metric_name VARCHAR(100) NOT NULL,
                metric_value FLOAT NOT NULL,  -- SIMULATING OLD SCHEMA
                metric_date DATE NOT NULL,
                components JSON,
                metadata JSON,
                created_at DATETIME
            )
        """))
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def async_session(async_engine):
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session

@pytest.mark.asyncio
async def test_flush_resilience_not_null_violation(async_session: AsyncSession):
    valid_metric = MarketMetric(
        company_id=1,
        analysis_id=1,
        metric_name="Valid Metric",
        metric_value=99.9,
        metric_date=datetime.date(2026, 10, 1)
    )
    
    invalid_metric = MarketMetric(
        company_id=1,
        analysis_id=1,
        metric_name="PageSpeed",
        metric_value=None,
        metric_date=datetime.date(2026, 10, 1)
    )
    
    async_session.add(valid_metric)
    async_session.add(invalid_metric)
    
    with pytest.raises(IntegrityError) as exc_info:
        await async_session.flush()
        
    assert "NOT NULL constraint failed" in str(exc_info.value)
    await async_session.rollback()
    
    m_dicts = [
        {"company_id": 1, "analysis_id": 1, "metric_name": "Valid Metric 2", "metric_value": 50.0, "metric_date": datetime.date(2026, 10, 1)},
        {"company_id": None, "analysis_id": 1, "metric_name": "Invalid Missing Company", "metric_value": 50.0, "metric_date": datetime.date(2026, 10, 1)},
        {"company_id": 1, "analysis_id": 1, "metric_name": None, "metric_value": 50.0, "metric_date": datetime.date(2026, 10, 1)}
    ]
    
    added = 0
    for m_dict in m_dicts:
        if m_dict.get("metric_name") is None or m_dict.get("company_id") is None:
            continue
        async_session.add(MarketMetric(**m_dict))
        added += 1
        
    assert added == 1
    await async_session.flush()
    await async_session.commit()
