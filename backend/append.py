import os

with open('app/api/routes/analytics.py', 'r', encoding='utf-8') as f:
    content = f.read()

dashboard_route = """

from typing import Optional
from app.repositories.companies import CompanyRepository
from app.repositories.insights import InsightRepository
from app.schemas.analysis import DashboardResponse

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    company_id: Optional[int] = Query(None, description="Filter dashboard by company ID"),
    db: AsyncSession = Depends(get_db),
):
    \"\"\"Get aggregated data for the Executive Overview dashboard.\"\"\"
    company = None
    if company_id:
        company_repo = CompanyRepository(db)
        company_doc = await company_repo.get_by_id(company_id)
        if company_doc:
            company = company_doc
            
    # MAI
    index_svc = MarketActivityIndexService(db)
    mai_data = None
    if company_id:
        mai_data = await index_svc.calculate(company_id)
        
    # Sentiment Summary (reuse logic from get_sentiment)
    sentiment_data = None
    if company_id:
        analysis_repo = AnalysisRepository(db)
        results = await analysis_repo.get_sentiments_by_company(company_id, limit=200)
        total = len(results)
        dist = {"positive": 0, "neutral": 0, "negative": 0}
        score_sum = 0.0
        for s in results:
            dist[s.label] = dist.get(s.label, 0) + 1
            score_sum += s.score
            
        sentiment_data = {
            "company_id": company_id,
            "total_documents": total,
            "positive": dist.get("positive", 0),
            "neutral": dist.get("neutral", 0),
            "negative": dist.get("negative", 0),
            "average_score": round(score_sum / max(total, 1), 4),
            "distribution": {k: round(v / max(total, 1), 4) for k, v in dist.items()},
        }
        
    # Emerging Signals
    signal_svc = EmergingSignalService(db)
    signals = []
    if company_id:
        signals = await signal_svc.detect_signals(company_id)
        
    # Top Topics
    top_topics = []
    if company_id:
        topics = await analysis_repo.get_topics_by_company(company_id, limit=5)
        top_topics = [TopicResponse.model_validate(t).model_dump() for t in topics]
        
    # Recent Insights
    recent_insights = []
    insight_repo = InsightRepository(db)
    docs, _ = await insight_repo.get_all(limit=5, company_id=company_id)
    recent_insights = docs

    return {
        "company": company,
        "market_activity": mai_data,
        "sentiment": sentiment_data,
        "signals": signals[:5],
        "top_topics": top_topics,
        "recent_insights": recent_insights,
    }
"""

if "def get_dashboard" not in content:
    content += dashboard_route
    with open('app/api/routes/analytics.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Dashboard endpoint appended.")
else:
    print("Dashboard endpoint already exists.")
