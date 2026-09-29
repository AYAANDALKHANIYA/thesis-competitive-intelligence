import os
import asyncio
import asyncpg

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    
    insights = await conn.fetch("SELECT id, company_id, insight_type, summary FROM insights WHERE analysis_id = 20 AND insight_type = 'AI Summary'")
    for i in insights:
        print(f"ID: {i['id']}, Company ID: {i['company_id']}, Type: {i['insight_type']}")
        print(f"Summary: {i['summary'][:50]}...")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
