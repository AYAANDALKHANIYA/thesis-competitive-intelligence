# 3. Complete API Endpoint Inventory

| Method | Endpoint | Purpose | Request | Response | DB-backed | Frontend Ready | Notes |
|---|---|---|---|---|---|---|---|
| GET | /health | Health | None | HealthResponse | No | Yes | |
| GET | /health/db | Health Db | None | DBHealthResponse | No | Yes | |
| GET | /health/sources | Health Sources | None | Unknown | No | Yes | |
| GET | /api/v1/companies | List Companies | Query: page, page_size, industry | PaginatedResponse_CompanyResponse_ | Yes | Yes | |
| POST | /api/v1/companies | Create Company | JSON Body | Unknown | Yes | Yes | |
| GET | /api/v1/companies/{company_id} | Get Company | None | CompanyResponse | Yes | Yes | |
| PATCH | /api/v1/companies/{company_id} | Update Company | JSON Body | CompanyResponse | Yes | Yes | |
| DELETE | /api/v1/companies/{company_id} | Delete Company | None | Unknown | Yes | Yes | |
| GET | /api/v1/sources | List Sources | Query: page, page_size, source_type | PaginatedResponse_SourceResponse_ | Yes | Yes | |
| POST | /api/v1/sources | Create Source | JSON Body | Unknown | Yes | Yes | |
| PATCH | /api/v1/sources/{source_id} | Update Source | JSON Body | SourceResponse | Yes | Yes | |
| GET | /api/v1/companies/{company_id}/competitors | List Competitors | None | Array[CompetitorResponse] | Yes | Yes | |
| POST | /api/v1/companies/{company_id}/competitors | Add Competitor | JSON Body | Unknown | Yes | Yes | |
| DELETE | /api/v1/companies/{company_id}/competitors/{competitor_id} | Remove Competitor | None | Unknown | Yes | Yes | |
| GET | /api/v1/documents | List Documents | Query: page, page_size, company_id, source_id, is_processed | PaginatedResponse_DocumentSummary_ | Yes | Yes | |
| GET | /api/v1/documents/{document_id} | Get Document | None | DocumentResponse | Yes | Yes | |
| GET | /api/v1/analytics/sentiment | Get Sentiment | Query: company_id, limit | Unknown | Yes | Yes | |
| GET | /api/v1/analytics/topics | Get Topics | Query: company_id, limit | Unknown | Yes | Yes | |
| GET | /api/v1/analytics/entities | Get Entities | Query: company_id, limit | Unknown | Yes | Yes | |
| GET | /api/v1/analytics/trends | Get Trends | Query: company_id, days | Unknown | Yes | Yes | |
| GET | /api/v1/analytics/signals | Get Signals | Query: company_id | Unknown | Yes | Yes | |
| GET | /api/v1/analytics/market-index | Get Market Index | Query: company_id | Unknown | Yes | Yes | |
| GET | /api/v1/predictions | List Predictions | Query: company_id, metric_name, limit | Array[PredictionResponse] | Yes | Yes | |
| GET | /api/v1/predictions/models | List Models | Query: model_name, status | Array[ModelVersionResponse] | Yes | Yes | |
| GET | /api/v1/predictions/models/{model_version_id} | Get Model Version | None | ModelVersionResponse | Yes | Yes | |
| GET | /api/v1/predictions/{company_id} | Get Company Predictions | Query: metric_name | Unknown | Yes | Yes | |
| GET | /api/v1/insights | List Insights | Query: company_id, insight_type, page, page_size | PaginatedResponse_InsightResponse_ | Yes | Yes | |
| GET | /api/v1/insights/{insight_id} | Get Insight | None | InsightResponse | Yes | Yes | |
| POST | /api/v1/insights/generate | Generate Insight | JSON Body | Unknown | Yes | Yes | |
| POST | /api/v1/ingestion/run | Trigger Ingestion | JSON Body | Unknown | Yes | Yes | |
| GET | /api/v1/ingestion/runs | List Ingestion Runs | Query: company_id, page, page_size | PaginatedResponse_IngestionRunResponse_ | Yes | Yes | |
| GET | /api/v1/ingestion/runs/{run_id} | Get Ingestion Run | None | IngestionRunResponse | Yes | Yes | |
| GET | /api/v1/system/stats | System Stats | None | SystemStatsResponse | Yes | Yes | |
| GET | /api/v1/system/source-health | Source Health | None | Unknown | No | Yes | |


# 5. Exact Frontend Data Contracts

### CompanyCreate
```json
{
  "name": "string",
  "domain": "string | null",
  "industry": "string | null",
  "description": "string | null",
  "country": "string | null",
  "ticker": "string | null",
  "sec_cik": "string | null",
}
```

### CompanyResponse
```json
{
  "id": "integer",
  "name": "string",
  "domain": "string | null",
  "industry": "string | null",
  "description": "string | null",
  "country": "string | null",
  "ticker": "string | null",
  "sec_cik": "string | null",
  "created_at": "string",
  "updated_at": "string",
}
```

### CompanyUpdate
```json
{
  "name": "string | null",
  "domain": "string | null",
  "industry": "string | null",
  "description": "string | null",
  "country": "string | null",
  "ticker": "string | null",
  "sec_cik": "string | null",
}
```

### CompetitorCreate
```json
{
  "competitor_id": "integer",
  "relationship_type": "string | null",
}
```

### CompetitorResponse
```json
{
  "id": "integer",
  "company_id": "integer",
  "competitor_id": "integer",
  "relationship_type": "string | null",
  "created_at": "string",
  "competitor_company": "CompanyResponse | null",
}
```

### DBHealthResponse
```json
{
  "status": "string",
  "latency_ms": "number",
}
```

### DocumentResponse
```json
{
  "id": "integer",
  "company_id": "integer",
  "source_id": "integer",
  "url": "string",
  "title": "string | null",
  "content": "string | null",
  "content_hash": "string | null",
  "author": "string | null",
  "published_at": "string | null",
  "collected_at": "string",
  "language": "string | null",
  "document_type": "string | null",
  "word_count": "integer | null",
  "is_processed": "boolean",
  "metadata_": "object | null",
  "created_at": "string",
  "updated_at": "string",
}
```

### DocumentSummary
```json
{
  "id": "integer",
  "company_id": "integer",
  "source_id": "integer",
  "url": "string",
  "title": "string | null",
  "published_at": "string | null",
  "collected_at": "string",
  "language": "string | null",
  "document_type": "string | null",
  "word_count": "integer | null",
  "is_processed": "boolean",
}
```

### HealthResponse
```json
{
  "status": "string",
  "environment": "string",
  "version": "string",
}
```

### IngestionRunResponse
```json
{
  "id": "integer",
  "company_id": "integer",
  "source_id": "integer | null",
  "started_at": "string",
  "completed_at": "string | null",
  "status": "string",
  "documents_found": "integer",
  "documents_new": "integer",
  "documents_changed": "integer",
  "documents_skipped": "integer",
  "requests_made": "integer",
  "errors": "integer",
}
```

### IngestionTriggerRequest
```json
{
  "company_id": "integer",
  "source_types": "array | null",
}
```

### InsightGenerateRequest
```json
{
  "insight_types": "array",
  "force": "boolean",
}
```

### InsightResponse
```json
{
  "id": "integer",
  "company_id": "integer",
  "insight_type": "string",
  "title": "string",
  "summary": "string",
  "severity": "string | null",
  "confidence": "number | null",
  "generated_at": "string",
  "model_name": "string | null",
  "model_version": "string | null",
  "evidence": "object | null",
}
```

### ModelVersionResponse
```json
{
  "id": "integer",
  "model_name": "string",
  "version": "string",
  "trained_at": "string",
  "training_samples": "integer | null",
  "features": "object | null",
  "mae": "number | null",
  "rmse": "number | null",
  "mape": "number | null",
  "status": "string",
  "metadata_": "object | null",
  "created_at": "string",
}
```

### PaginatedResponse_CompanyResponse_
```json
{
  "items": "Array[CompanyResponse]",
  "total": "integer",
  "page": "integer",
  "page_size": "integer",
  "total_pages": "integer",
}
```

### PaginatedResponse_DocumentSummary_
```json
{
  "items": "Array[DocumentSummary]",
  "total": "integer",
  "page": "integer",
  "page_size": "integer",
  "total_pages": "integer",
}
```

### PaginatedResponse_IngestionRunResponse_
```json
{
  "items": "Array[IngestionRunResponse]",
  "total": "integer",
  "page": "integer",
  "page_size": "integer",
  "total_pages": "integer",
}
```

### PaginatedResponse_InsightResponse_
```json
{
  "items": "Array[InsightResponse]",
  "total": "integer",
  "page": "integer",
  "page_size": "integer",
  "total_pages": "integer",
}
```

### PaginatedResponse_SourceResponse_
```json
{
  "items": "Array[SourceResponse]",
  "total": "integer",
  "page": "integer",
  "page_size": "integer",
  "total_pages": "integer",
}
```

### PredictionResponse
```json
{
  "id": "integer",
  "company_id": "integer",
  "metric_name": "string",
  "prediction_date": "string",
  "horizon_days": "integer",
  "predicted_value": "number",
  "lower_bound": "number | null",
  "upper_bound": "number | null",
  "model_version_id": "integer | null",
  "created_at": "string",
}
```

### SourceCreate
```json
{
  "name": "string",
  "source_type": "string",
  "base_url": "string | null",
  "enabled": "boolean",
  "rate_limit_per_minute": "integer",
  "crawl_delay_seconds": "number",
  "config": "object | null",
}
```

### SourceResponse
```json
{
  "id": "integer",
  "name": "string",
  "source_type": "string",
  "base_url": "string | null",
  "enabled": "boolean",
  "rate_limit_per_minute": "integer",
  "crawl_delay_seconds": "number",
  "config": "object | null",
  "created_at": "string",
  "updated_at": "string",
}
```

### SourceUpdate
```json
{
  "name": "string | null",
  "base_url": "string | null",
  "enabled": "boolean | null",
  "rate_limit_per_minute": "integer | null",
  "crawl_delay_seconds": "number | null",
  "config": "object | null",
}
```

### SystemStatsResponse
```json
{
  "total_companies": "integer",
  "total_documents": "integer",
  "total_processed": "integer",
  "total_sources": "integer",
  "total_ingestion_runs": "integer",
  "total_predictions": "integer",
  "total_insights": "integer",
  "total_sentiment_results": "integer",
  "total_topics": "integer",
  "total_entities": "integer",
}
```

