import os
import asyncio
import asyncpg
import json
from datetime import datetime

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)

    print("--- ANALYSIS RUNS ---")
    rows = await conn.fetch("SELECT id, status, started_at, completed_at, company_id FROM analysis_runs ORDER BY id DESC LIMIT 5")
    for row in rows:
        print(dict(row))
    
    print("\n--- INGESTION RUNS ---")
    rows = await conn.fetch("SELECT id, status, started_at, completed_at, documents_collected, documents_failed FROM ingestion_runs ORDER BY id DESC LIMIT 5")
    for row in rows:
        print(dict(row))

    print("\n--- DOCUMENTS PER COMPANY ---")
    rows = await conn.fetch('''
        SELECT c.name, COUNT(d.id) as cnt 
        FROM documents d 
        JOIN companies c ON d.company_id = c.id 
        GROUP BY c.name
    ''')
    for row in rows:
        print(dict(row))

    print("\n--- SOURCE TYPES ---")
    rows = await conn.fetch('''
        SELECT s.source_type, COUNT(d.id) as cnt 
        FROM documents d 
        JOIN sources s ON d.source_id = s.id 
        GROUP BY s.source_type
    ''')
    for row in rows:
        print(dict(row))

    print("\n--- DUPLICATES ---")
    # if duplicate detection is stored
    try:
        val = await conn.fetchval("SELECT count(*) FROM documents WHERE is_processed = false")
        print(f"Unprocessed docs: {val}")
    except Exception as e:
        print(f"Error checking duplicates: {e}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
