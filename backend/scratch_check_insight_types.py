import os
import asyncio
import asyncpg

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    
    insights = await conn.fetch("SELECT distinct insight_type FROM insights WHERE analysis_id = 20")
    print(f"Insight types: {[i['insight_type'] for i in insights]}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
