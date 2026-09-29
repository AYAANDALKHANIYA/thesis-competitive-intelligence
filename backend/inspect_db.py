import asyncio
import sys
import json
sys.path.insert(0, '.')
from app.db.session import async_session_factory
from sqlalchemy import text

async def inspect():
    async with async_session_factory() as session:
        res = await session.execute(text("SELECT id, name FROM companies WHERE name IN ('Semrush', 'Ahrefs', 'Moz')"))
        companies = {row[1]: row[0] for row in res.fetchall()}
        
        print("=== DATABASE INSPECTION ===")
        print("Companies:", companies)
        
        res = await session.execute(text("SELECT id, status, started_at FROM analysis_runs ORDER BY started_at DESC NULLS LAST LIMIT 5"))
        runs = res.fetchall()
        print("\nLatest Analysis Runs:")
        for r in runs:
            print(f"- ID: {r[0]}, Status: {r[1]}, Started: {r[2]}")
            res_comp = await session.execute(text("SELECT competitor_id FROM analysis_competitors WHERE analysis_run_id = :aid"), {"aid": r[0]})
            comps = res_comp.fetchall()
            print(f"  Competitors: {[c[0] for c in comps]}")

        for c_name, c_id in companies.items():
            print(f"\n--- {c_name} (ID: {c_id}) ---")
            
            docs = await session.execute(text("SELECT COUNT(*), COUNT(published_at) FROM documents WHERE company_id = :cid"), {"cid": c_id})
            doc_stats = docs.fetchone()
            print(f"Documents: {doc_stats[0]} (Dated: {doc_stats[1]})")
            
            doc_types = await session.execute(text("SELECT document_type, COUNT(*) FROM documents WHERE company_id = :cid GROUP BY document_type"), {"cid": c_id})
            print(f"Doc Types: {doc_types.fetchall()}")
            url_count = await session.execute(text("SELECT COUNT(url) FROM documents WHERE company_id = :cid AND url IS NOT NULL"), {"cid": c_id})
            print(f"URL Count: {url_count.fetchone()[0]}")
            
            mets = await session.execute(text("SELECT metric_name, COUNT(*) FROM market_metrics WHERE company_id = :cid GROUP BY metric_name"), {"cid": c_id})
            print(f"Metrics Rows: {mets.fetchall()}")
            
            sents = await session.execute(text("SELECT COUNT(*) FROM sentiment_results sr JOIN documents d ON sr.document_id = d.id WHERE d.company_id = :cid"), {"cid": c_id})
            print(f"Sentiment Rows: {sents.fetchone()[0]}")
            
            topics = await session.execute(text("SELECT COUNT(*) FROM document_topics dt JOIN documents d ON dt.document_id = d.id WHERE d.company_id = :cid"), {"cid": c_id})
            print(f"Topic Rows (in document_topics): {topics.fetchone()[0]}")
            
            ins = await session.execute(text("SELECT insight_type, COUNT(*) FROM insights WHERE company_id = :cid GROUP BY insight_type"), {"cid": c_id})
            print(f"Insight Rows: {ins.fetchall()}")

asyncio.run(inspect())
