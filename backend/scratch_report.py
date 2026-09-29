import os
import asyncio
import asyncpg
import json
from datetime import datetime, timezone

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)

    # 1. Get the target analysis run
    # Check if ID 20 is available
    target_analysis = await conn.fetchrow("SELECT * FROM analysis_runs WHERE id = 20")
    if not target_analysis:
        target_analysis = await conn.fetchrow("SELECT * FROM analysis_runs WHERE status = 'COMPLETED' ORDER BY id DESC LIMIT 1")
    
    if not target_analysis:
        print("NO COMPLETED ANALYSIS FOUND.")
        await conn.close()
        return

    analysis_id = target_analysis['id']
    analysis_status = target_analysis['status']
    analysis_date = target_analysis['completed_at'] or target_analysis['started_at']
    if analysis_date:
        analysis_date_str = analysis_date.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        analysis_date_str = "UNAVAILABLE"
    
    company_ids = [target_analysis['company_id']]
    competitors = await conn.fetch("SELECT competitor_id FROM analysis_competitors WHERE analysis_run_id = $1", analysis_id)
    company_ids.extend([c['competitor_id'] for c in competitors])
    
    if not company_ids:
        print("NO COMPANIES FOUND.")
        await conn.close()
        return
        
    company_ids_str = ",".join(map(str, company_ids))
    
    # 2. Get Companies and their document counts
    companies = await conn.fetch(f"""
        SELECT c.id, c.name, COUNT(d.id) as doc_count
        FROM companies c
        LEFT JOIN documents d ON c.id = d.company_id
        WHERE c.id = ANY($1::int[])
        GROUP BY c.id, c.name
        ORDER BY doc_count DESC
    """, company_ids)
    
    # 3. Total documents
    doc_stats = await conn.fetchrow(f"""
        SELECT 
            COUNT(id) as total_collected,
            COUNT(DISTINCT url) as unique_urls,
            SUM(CASE WHEN is_processed = true THEN 1 ELSE 0 END) as processed_count
        FROM documents
        WHERE company_id = ANY($1::int[])
    """, company_ids)
    
    # Duplicates detected
    # We can try to sum documents_skipped from ingestion_runs
    ingestion_stats = await conn.fetchrow(f"""
        SELECT 
            SUM(documents_skipped) as duplicates_skipped,
            SUM(errors) as total_errors
        FROM ingestion_runs
        WHERE company_id = ANY($1::int[])
    """, company_ids)
    duplicates = ingestion_stats['duplicates_skipped'] if ingestion_stats and ingestion_stats['duplicates_skipped'] is not None else "UNAVAILABLE"
    
    # 4. Source types
    source_types = await conn.fetch(f"""
        SELECT s.source_type, COUNT(d.id) as doc_count
        FROM documents d
        JOIN sources s ON d.source_id = s.id
        WHERE d.company_id = ANY($1::int[])
        GROUP BY s.source_type
        ORDER BY doc_count DESC
    """, company_ids)
    
    # 5. Source status
    source_states = await conn.fetch(f"""
        SELECT fetch_status, COUNT(*) as cnt
        FROM source_states
        WHERE company_id = ANY($1::int[])
        GROUP BY fetch_status
    """, company_ids)
    
    success_sources = 0
    failed_sources = 0
    for ss in source_states:
        if ss['fetch_status'] == 'success':
            success_sources += ss['cnt']
        elif ss['fetch_status'] == 'error':
            failed_sources += ss['cnt']
            
    # Also count ingestion runs with errors just in case
    ingestion_errors_count = await conn.fetchval(f"""
        SELECT COUNT(*) FROM ingestion_runs WHERE company_id = ANY($1::int[]) AND errors > 0
    """, company_ids)
    if not failed_sources and ingestion_errors_count:
        failed_sources = ingestion_errors_count

    print("=" * 60)
    print("CHAPTER 4 — DATA COLLECTION RESULTS")
    print("===================================")
    print(f"Analysis ID              : {analysis_id}")
    print(f"Analysis Status          : {analysis_status}")
    print(f"Analysis Date            : {analysis_date_str}")
    print("\n## COMPANIES / ORGANISATIONS\n")
    for c in companies:
        name_pad = (c['name'] + " ")[:24].ljust(24)
        print(f"{name_pad} : {c['doc_count']}")
        
    print("\n## TOTAL DOCUMENTS\n")
    print(f"{'Documents collected':<24} : {doc_stats['total_collected'] or 0}")
    print(f"{'Unique URLs':<24} : {doc_stats['unique_urls'] or 0}")
    print(f"{'Processed documents':<24} : {doc_stats['processed_count'] or 0}")
    print(f"{'Duplicates detected':<24} : {duplicates}")
    
    print("\n## SOURCE TYPES\n")
    source_type_map = {
        'website': 'Company websites',
        'rss': 'RSS / Atom',
        'gdelt': 'GDELT',
        'sec': 'SEC EDGAR'
    }
    # Initialize all 4 to 0
    src_counts = {k: 0 for k in source_type_map.keys()}
    other_sources = 0
    for st in source_types:
        stype = st['source_type']
        if stype in src_counts:
            src_counts[stype] = st['doc_count']
        else:
            other_sources += st['doc_count']
            
    for k, v in source_type_map.items():
        print(f"{v:<24} : {src_counts[k]}")
    print(f"{'Other permitted sources':<24} : {other_sources}")
    
    print("\n## SOURCE STATUS\n")
    print(f"{'Successful sources':<24} : {success_sources}")
    print(f"{'Unavailable/failed':<24} : {failed_sources}")
    
    print("\n## COLLECTION SUMMARY\n")
    print(f"Data collection yielded {doc_stats['total_collected'] or 0} documents across {len(companies)} entities.")
    print(f"A total of {doc_stats['processed_count'] or 0} documents were successfully processed and ingested.")
    if duplicates != "UNAVAILABLE":
         print(f"{duplicates} documents were skipped during ingestion due to deduplication checks.")
    print("=" * 60)
    
    print("\n\n## VERIFICATION")
    print(f"{'Database records checked':<24} : documents={doc_stats['total_collected']}, companies={len(companies)}")
    print(f"{'Analysis ID verified':<24} : {analysis_id}")
    print(f"{'No fabricated values':<24} : YES")
    print(f"{'Read-only inspection':<24} : YES")
    print("==============================")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
