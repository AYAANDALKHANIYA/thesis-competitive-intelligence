import os
import asyncio
import asyncpg

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    rows = await conn.fetch("SELECT id, name, is_primary FROM companies WHERE name IN ('Semrush', 'Moz', 'Ahrefs')")
    for r in rows:
        print(dict(r))
    
    # Also let's check analysis 20 to see which is primary and which is competitor
    analysis = await conn.fetchrow("SELECT company_id FROM analysis_runs WHERE id=20")
    if analysis:
        primary_id = analysis['company_id']
        print(f"Primary Company ID for Analysis 20: {primary_id}")
        competitors = await conn.fetch("SELECT competitor_id FROM analysis_competitors WHERE analysis_run_id=20")
        print(f"Competitor IDs for Analysis 20: {[c['competitor_id'] for c in competitors]}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
