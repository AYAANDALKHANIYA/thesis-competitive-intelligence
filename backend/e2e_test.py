import httpx
import asyncio
import json

async def run_e2e_test():
    client = httpx.AsyncClient(base_url="http://localhost:8000", timeout=60.0)
    
    print("1. Testing POST /api/v1/system/setup")
    setup_payload = {
        "company_name": "Curato",
        "company_domain": "https://curato.ai",
        "industry": "Content Curation",
        "competitors": [
            {"name": "Breef", "domain": "https://www.breef.com"},
            {"name": "DesignRush", "domain": "https://www.designrush.com"}
        ]
    }
    r = await client.post("/api/v1/system/setup", json=setup_payload)
    print("Setup Status:", r.status_code)
    try:
        config = r.json()
        print("Setup Response:", json.dumps(config, indent=2))
        primary_id = config.get("primary_company", {}).get("id")
        if not primary_id:
            print("Failed to get primary_id")
            return
    except Exception as e:
        print("Error parsing setup response:", e)
        print("Raw:", r.text)
        return
        
    print("\n2. Testing POST /api/v1/companies/{company_id}/collect")
    r = await client.post(f"/api/v1/companies/{primary_id}/collect", timeout=60.0)
    print("Collect Status:", r.status_code)
    try:
        collect_res = r.json()
        print("Collect Response:", json.dumps(collect_res, indent=2))
    except Exception as e:
        print("Error parsing collect response:", e)
        print("Raw:", r.text)
        
    print("\n3. Testing GET /api/v1/analytics/dashboard")
    r = await client.get("/api/v1/analytics/dashboard")
    print("Dashboard Status:", r.status_code)
    try:
        dashboard = r.json()
        print("Dashboard keys:", dashboard.keys())
        print("Market Activity:", dashboard.get("market_activity"))
        print("Sentiment:", dashboard.get("sentiment"))
    except Exception as e:
        print("Error parsing dashboard response:", e)
        print("Raw:", r.text)

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
