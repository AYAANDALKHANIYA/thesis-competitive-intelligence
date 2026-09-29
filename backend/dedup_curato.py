import asyncio
from app.db.session import async_session_factory
from sqlalchemy import text

async def run():
    async with async_session_factory() as db:
        print("Starting deduplication of Curato (ID 8 -> ID 9)")
        
        # 1. Update Competitors (company_id)
        res1 = await db.execute(text("UPDATE competitors SET company_id = 9 WHERE company_id = 8"))
        print(f"Updated {res1.rowcount} competitors where company_id = 8")
        
        # 2. Update Competitors (competitor_id)
        res2 = await db.execute(text("UPDATE competitors SET competitor_id = 9 WHERE competitor_id = 8"))
        print(f"Updated {res2.rowcount} competitors where competitor_id = 8")
        
        # 3. Update Documents
        res3 = await db.execute(text("UPDATE documents SET company_id = 9 WHERE company_id = 8"))
        print(f"Updated {res3.rowcount} documents where company_id = 8")
        
        # 4. Update Source States
        res4 = await db.execute(text("UPDATE source_states SET company_id = 9 WHERE company_id = 8"))
        print(f"Updated {res4.rowcount} source_states where company_id = 8")
        
        # 5. Update Market Metrics
        res5 = await db.execute(text("UPDATE market_metrics SET company_id = 9 WHERE company_id = 8"))
        print(f"Updated {res5.rowcount} market_metrics where company_id = 8")
        
        # 6. Update Predictions
        res6 = await db.execute(text("UPDATE predictions SET company_id = 9 WHERE company_id = 8"))
        print(f"Updated {res6.rowcount} predictions where company_id = 8")
        
        # 7. Update Ingestion Runs
        res7 = await db.execute(text("UPDATE ingestion_runs SET company_id = 9 WHERE company_id = 8"))
        print(f"Updated {res7.rowcount} ingestion_runs where company_id = 8")
        
        # 8. Update Insights
        res8 = await db.execute(text("UPDATE insights SET company_id = 9 WHERE company_id = 8"))
        print(f"Updated {res8.rowcount} insights where company_id = 8")
        
        # 9. Delete ID 8
        res9 = await db.execute(text("DELETE FROM companies WHERE id = 8"))
        print(f"Deleted ID 8, rowcount: {res9.rowcount}")
        
        await db.commit()
        print("Deduplication complete and committed.")

if __name__ == "__main__":
    asyncio.run(run())
