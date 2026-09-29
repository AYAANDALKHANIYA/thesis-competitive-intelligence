"""Integration tests for health and company API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_db(client: AsyncClient):
    response = await client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"


@pytest.mark.asyncio
async def test_create_company(client: AsyncClient):
    response = await client.post("/api/v1/companies", json={
        "name": "Test Company",
        "domain": "test.com",
        "industry": "Technology",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Company"
    assert data["domain"] == "test.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_companies(client: AsyncClient):
    # Create a company first
    await client.post("/api/v1/companies", json={"name": "Listed Company"})

    response = await client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_company(client: AsyncClient):
    create_resp = await client.post("/api/v1/companies", json={"name": "Get Me"})
    company_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Me"


@pytest.mark.asyncio
async def test_update_company(client: AsyncClient):
    create_resp = await client.post("/api/v1/companies", json={"name": "Original"})
    company_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/companies/{company_id}",
        json={"name": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_company(client: AsyncClient):
    create_resp = await client.post("/api/v1/companies", json={"name": "Delete Me"})
    company_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/companies/{company_id}")
    assert response.status_code == 204

    get_resp = await client.get(f"/api/v1/companies/{company_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_company_not_found(client: AsyncClient):
    response = await client.get("/api/v1/companies/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_system_stats(client: AsyncClient):
    response = await client.get("/api/v1/system/configuration")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data


@pytest.mark.asyncio
async def test_list_sources(client: AsyncClient):
    response = await client.get("/api/v1/sources")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient):
    response = await client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_analytics_sentiment(client: AsyncClient):
    response = await client.post("/api/v1/system/setup", json={
        "company_name": "Analytics Co",
        "company_domain": "analytics.com",
    })
    company_id = response.json()["primary_company"]["id"]

    response = await client.get(f"/api/v1/analytics/sentiment?company_id={company_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_predictions(client: AsyncClient):
    response = await client.get("/api/v1/predictions")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_insights(client: AsyncClient):
    response = await client.get("/api/v1/insights")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
