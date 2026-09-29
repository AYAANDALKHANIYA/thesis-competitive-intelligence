import os
import asyncio
import asyncpg

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    
    insights = await conn.fetch("SELECT id, company_id, title, summary, confidence, evidence FROM insights WHERE analysis_id = 20 AND insight_type = 'Growth Signal'")
    for i in insights:
        print(f"ID: {i['id']}, Company ID: {i['company_id']}, Title: {i['title']}")
        print(f"Summary: {i['summary']}")
        print(f"Evidence: {i['evidence']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
