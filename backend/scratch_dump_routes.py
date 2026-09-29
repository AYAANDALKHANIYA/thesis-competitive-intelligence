import json
import sys
from fastapi.routing import APIRoute

# Adjust path to import app
sys.path.insert(0, r"c:\Users\ayaan\OneDrive\Desktop\AI POWERED COMPETETIVE INTELLIGENCE & MARKET TREND PREDICTION PLATFORM\backend")

try:
    from app.main import app
    
    endpoints = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            endpoints.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name,
                "module": route.endpoint.__module__ if hasattr(route.endpoint, "__module__") else ""
            })
            
    with open("c:/Users/ayaan/OneDrive/Desktop/AI POWERED COMPETETIVE INTELLIGENCE & MARKET TREND PREDICTION PLATFORM/backend/scratch_routes.json", "w") as f:
        json.dump(endpoints, f, indent=2)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
