import asyncio
from sqlalchemy import text
from app.db.session import engine

async def alter_table():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE market_metrics ALTER COLUMN metric_value DROP NOT NULL;"))
    print("Altered market_metrics.metric_value to allow NULL.")

if __name__ == "__main__":
    asyncio.run(alter_table())
