import asyncio
import sys
import json
sys.path.insert(0, '.')
from app.db.session import async_session_factory
from sqlalchemy import text
from decimal import Decimal

async def get_report():
    async with async_session_factory() as session:
        # Get Companies
        res = await session.execute(text("SELECT id, name FROM companies WHERE name IN ('Semrush', 'Ahrefs', 'Moz')"))
        companies = {row[1]: row[0] for row in res.fetchall()}

        report_data = {}

        for c_name, c_id in companies.items():
            data = {}
            
            # Ingestion Runs
            runs = await session.execute(text(
                "SELECT SUM(documents_found), SUM(documents_new), SUM(documents_skipped), SUM(documents_changed) FROM ingestion_runs WHERE company_id = :cid"
            ), {"cid": c_id})
            run_stats = runs.fetchone()
            data['pages_crawled'] = run_stats[0] if run_stats and run_stats[0] is not None else 'UNAVAILABLE'
            data['documents_collected'] = run_stats[1] if run_stats and run_stats[1] is not None else 0
            data['documents_skipped'] = run_stats[2] if run_stats and run_stats[2] is not None else 0
            data['documents_updated'] = run_stats[3] if run_stats and run_stats[3] is not None else 0

            # Documents
            docs = await session.execute(text(
                "SELECT COUNT(*), COUNT(published_at) FROM documents WHERE company_id = :cid"
            ), {"cid": c_id})
            doc_stats = docs.fetchone()
            data['actual_docs'] = doc_stats[0] if doc_stats else 0
            data['dated_docs'] = doc_stats[1] if doc_stats else 0
            
            # Topics
            topics = await session.execute(text(
                "SELECT t.name FROM topics t JOIN document_topics dt ON t.id = dt.topic_id JOIN documents d ON d.id = dt.document_id WHERE d.company_id = :cid"
            ), {"cid": c_id})
            topic_rows = topics.fetchall()
            topic_names = list(set([r[0] for r in topic_rows]))
            data['topics'] = ", ".join(topic_names) if topic_names else "INSUFFICIENT DATA"
            data['topic_count'] = len(topic_names) if topic_names else "0"
            data['topic_momentum'] = "UNAVAILABLE"

            # Sentiment
            sents = await session.execute(text(
                "SELECT label, score FROM sentiment_results sr JOIN documents d ON sr.document_id = d.id WHERE d.company_id = :cid"
            ), {"cid": c_id})
            sent_rows = sents.fetchall()
            pos = sum(1 for r in sent_rows if r[0] == 'positive')
            neu = sum(1 for r in sent_rows if r[0] == 'neutral')
            neg = sum(1 for r in sent_rows if r[0] == 'negative')
            data['sentiment_counts'] = f"Pos: {pos}, Neu: {neu}, Neg: {neg}"
            avg_sent = sum(float(r[1]) for r in sent_rows)/len(sent_rows) if sent_rows else None
            data['average_sentiment'] = round(avg_sent, 2) if avg_sent is not None else "INSUFFICIENT DATA"

            # Metrics
            mets = await session.execute(text(
                "SELECT metric_name, metric_value, components FROM market_metrics WHERE company_id = :cid AND metric_name = 'market_activity_index' ORDER BY metric_date DESC LIMIT 1"
            ), {"cid": c_id})
            met_row = mets.fetchone()
            if met_row:
                data['mai'] = round(float(met_row[1]), 2)
                comp = met_row[2] if met_row[2] else {}
                if isinstance(comp, str): comp = json.loads(comp)
                data['content_activity'] = round(float(comp.get('content_activity', 0)), 2) if 'content_activity' in comp else 'UNAVAILABLE'
                data['review_activity'] = round(float(comp.get('review_activity', 0)), 2) if 'review_activity' in comp else 'UNAVAILABLE'
                data['tech_seo'] = round(float(comp.get('technical_seo_score', 0)), 2) if 'technical_seo_score' in comp else 'UNAVAILABLE'
                
                avail = [k for k,v in comp.items() if v is not None]
                unavail = [k for k,v in comp.items() if v is None]
                data['avail_comps'] = len(avail)
                data['unavail_comps'] = len(unavail)
            else:
                data['mai'] = "INSUFFICIENT DATA"
                data['content_activity'] = "UNAVAILABLE"
                data['review_activity'] = "UNAVAILABLE"
                data['tech_seo'] = "UNAVAILABLE"
                data['avail_comps'] = "UNAVAILABLE"
                data['unavail_comps'] = "UNAVAILABLE"

            # Temporal comparison
            mets_all = await session.execute(text(
                "SELECT metric_value FROM market_metrics WHERE company_id = :cid AND metric_name = 'market_activity_index' ORDER BY metric_date ASC"
            ), {"cid": c_id})
            mets_all_rows = mets_all.fetchall()
            if len(mets_all_rows) > 1:
                data['temporal'] = "AVAILABLE (Trended)"
            else:
                data['temporal'] = "INSUFFICIENT DATA"

            # Prediction
            pred = await session.execute(text(
                "SELECT COUNT(*) FROM market_metrics WHERE company_id = :cid AND metric_name = 'market_activity_index'"
            ), {"cid": c_id})
            pred_count = pred.fetchone()[0]
            if pred_count >= 30:
                data['prediction'] = "SUFFICIENT"
            else:
                data['prediction'] = "INSUFFICIENT DATA"

            # Insights
            ins = await session.execute(text(
                "SELECT title, summary, confidence, evidence FROM insights WHERE company_id = :cid"
            ), {"cid": c_id})
            ins_rows = ins.fetchall()
            if ins_rows:
                data['growth_signals'] = len(ins_rows)
                
                total_ev = 0
                for r in ins_rows:
                    ev = r[3]
                    if isinstance(ev, str): ev = json.loads(ev)
                    if ev and isinstance(ev, list): total_ev += len(ev)
                    elif ev and isinstance(ev, dict): total_ev += len(ev)

                data['growth_evidence'] = total_ev
                
                conf = [float(r[2]) for r in ins_rows if r[2] is not None]
                data['growth_confidence'] = round(sum(conf)/len(conf), 2) if conf else "UNAVAILABLE"
            else:
                data['growth_signals'] = "0"
                data['growth_evidence'] = "0"
                data['growth_confidence'] = "INSUFFICIENT DATA"
            
            data['pagespeed'] = "UNAVAILABLE"
            data['llm_status'] = "Active"
            data['unified_evidence'] = "UNAVAILABLE" # Will calculate from evidence tables if exists

            report_data[c_name] = data

        print(json.dumps(report_data, indent=2))

asyncio.run(get_report())
