import os
import asyncio
import asyncpg
from datetime import datetime

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    
    # 1. Target Analysis ID 20
    analysis = await conn.fetchrow("SELECT * FROM analysis_runs WHERE id = 20")
    
    if not analysis:
        print("Analysis 20 not found.")
        await conn.close()
        return

    started_at = analysis['started_at']
    completed_at = analysis['completed_at']
    primary_company_id = analysis['company_id']
    
    # 2. Competitors
    competitor_rows = await conn.fetch("SELECT competitor_id FROM analysis_competitors WHERE analysis_run_id = 20")
    competitor_ids = [r['competitor_id'] for r in competitor_rows]
    all_company_ids = [primary_company_id] + competitor_ids
    
    # Fetch company names
    companies_dict = {}
    c_rows = await conn.fetch("SELECT id, name FROM companies WHERE id = ANY($1::int[])", all_company_ids)
    for r in c_rows:
        companies_dict[r['id']] = r['name']
        
    primary_name = companies_dict.get(primary_company_id, "Unknown")
    c1_name = companies_dict.get(competitor_ids[0], "Unknown") if len(competitor_ids) > 0 else "None"
    c2_name = companies_dict.get(competitor_ids[1], "Unknown") if len(competitor_ids) > 1 else "None"
    
    print(f"Primary company: {primary_name}")
    print(f"Competitor 1: {c1_name}")
    print(f"Competitor 2: {c2_name}")
    
    # Documents per company
    doc_counts = {}
    d_rows = await conn.fetch("SELECT company_id, count(id) as c FROM documents WHERE company_id = ANY($1::int[]) GROUP BY company_id", all_company_ids)
    for r in d_rows:
        doc_counts[r['company_id']] = r['c']
        
    primary_docs = doc_counts.get(primary_company_id, 0)
    c1_docs = doc_counts.get(competitor_ids[0], 0) if len(competitor_ids) > 0 else 0
    c2_docs = doc_counts.get(competitor_ids[1], 0) if len(competitor_ids) > 1 else 0
    
    print(f"Primary company documents: {primary_docs}")
    print(f"Competitor 1 documents: {c1_docs}")
    print(f"Competitor 2 documents: {c2_docs}")
    
    # Total associated docs (45)
    total_docs = sum(doc_counts.values())
    print(f"Documents associated with complete analysis: {total_docs}")
    
    unique_urls = await conn.fetchval("SELECT count(distinct url) FROM documents WHERE company_id = ANY($1::int[])", all_company_ids)
    processed = await conn.fetchval("SELECT count(*) FROM documents WHERE company_id = ANY($1::int[]) AND is_processed=true", all_company_ids)
    
    print(f"Unique URLs: {unique_urls}")
    print(f"Processed documents: {processed}")
    
    # Check ingestion runs during this analysis time frame
    # We define "during this run" as ingestion runs that started after the analysis started, or within a few minutes before
    ingestion_docs_new = await conn.fetchval("""
        SELECT COALESCE(sum(documents_new), 0) FROM ingestion_runs 
        WHERE company_id = ANY($1::int[]) 
        AND started_at >= $2 AND started_at <= COALESCE($3, now())
    """, all_company_ids, started_at, completed_at)
    
    # If ingestion wasn't triggered by analysis, check if there are any ingestion_runs at all
    ingestion_docs_total = await conn.fetchval("SELECT COALESCE(sum(documents_new), 0) FROM ingestion_runs WHERE company_id = ANY($1::int[])", all_company_ids)
    
    print(f"Documents collected during this run (strict time): {ingestion_docs_new}")
    print(f"Documents collected by all ingestion runs ever: {ingestion_docs_total}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
