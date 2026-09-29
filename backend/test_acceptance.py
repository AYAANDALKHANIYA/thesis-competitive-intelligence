import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_test():
    print("Starting Acceptance Test...")
    
    # Trigger analysis
    payload = {
        "company": {
            "name": "Curato",
            "website": "https://curato.ai"
        },
        "competitors": [
            {
                "name": "Breef",
                "website": "https://breef.com"
            },
            {
                "name": "DesignRush",
                "website": "https://designrush.com"
            }
        ]
    }
    
    res = client.post("/api/v1/analysis", json=payload)
    if res.status_code != 200:
        print("Failed to start analysis:", res.text)
        return
        
    data = res.json()
    analysis_id = data["analysis_id"]
    print(f"Analysis started. ID: {analysis_id}")
    
    import time
    status = "QUEUED"
    for _ in range(60): # Wait up to 60 seconds
        res = client.get(f"/api/v1/analysis/{analysis_id}")
        status_data = res.json()
        status = status_data["status"]
        print(f"Status: {status}")
        if status in ["COMPLETED", "PARTIAL", "FAILED"]:
            break
        time.sleep(2)
        
    print("\n--- RESULTS ---")
    
    # Overview
    res = client.get(f"/api/v1/analysis/{analysis_id}/overview")
    print("Overview:", res.json())
    
    # Competitors
    res = client.get(f"/api/v1/analysis/{analysis_id}/competitors")
    print("Competitors:", res.json())
    
    # SEO
    res = client.get(f"/api/v1/analysis/{analysis_id}/seo")
    print("SEO:", res.json())
    
    # Performance
    res = client.get(f"/api/v1/analysis/{analysis_id}/performance")
    print("Performance:", res.json())
    
    # Growth
    res = client.get(f"/api/v1/analysis/{analysis_id}/growth-signals")
    print("Growth:", res.json())
    
    # Evidence
    res = client.get(f"/api/v1/analysis/{analysis_id}/evidence")
    print("Evidence count:", len(res.json()))

if __name__ == "__main__":
    run_test()
