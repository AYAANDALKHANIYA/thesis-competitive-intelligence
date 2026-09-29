import zlib
import base64
import requests
import os

mermaid_code = """erDiagram
    %% CENTRAL AREA
    companies {
        integer id PK
        string name
        string domain
        string industry
        boolean is_primary
    }

    analysis_runs {
        integer id PK
        integer company_id FK
        string status
        jsonb metadata
        text error_summary
    }

    documents {
        integer id PK
        integer company_id FK
        integer source_id FK
        text url
        text content
        string document_type
        boolean is_processed
    }

    %% DATA COLLECTION
    sources {
        integer id PK
        string name
        string source_type
        text base_url
    }

    source_states {
        integer id PK
        integer source_id FK
        integer company_id FK
        text url
        string fetch_status
        integer error_count
    }

    ingestion_runs {
        integer id PK
        integer company_id FK
        integer source_id FK
        string status
        integer documents_found
    }

    document_versions {
        integer id PK
        integer document_id FK
        integer version_number
        text content
    }

    %% NLP
    topics {
        integer id PK
        string name
        jsonb keywords
        integer document_count
    }

    document_topics {
        integer id PK
        integer document_id FK
        integer topic_id FK
        float probability
    }

    sentiment_results {
        integer id PK
        integer document_id FK
        integer analysis_id FK
        string label
        float score
        float confidence
    }

    entities {
        integer id PK
        integer document_id FK
        string entity_text
        string entity_type
    }

    embeddings {
        integer id PK
        integer document_id FK
        string embedding
        string model_name
    }

    %% ANALYTICS
    analysis_competitors {
        integer id PK
        integer analysis_run_id FK
        integer competitor_id FK
    }

    market_metrics {
        integer id PK
        integer company_id FK
        integer analysis_id FK
        string metric_name
        float metric_value
        jsonb components
    }

    insights {
        integer id PK
        integer company_id FK
        integer analysis_id FK
        string insight_type
        string title
        text summary
        jsonb evidence
    }

    %% PREDICTION
    model_versions {
        integer id PK
        string model_name
        string version
        string status
    }

    predictions {
        integer id PK
        integer company_id FK
        integer model_version_id FK
        string metric_name
        float predicted_value
        integer horizon_days
    }

    %% OTHER SOURCE DATA
    reviews {
        integer id PK
        integer company_id FK
        string source
        float rating
        text review_text
    }

    competitors {
        integer id PK
        integer company_id FK
        integer competitor_id FK
        string relationship_type
    }

    %% RELATIONSHIPS
    companies ||--o{ competitors : "company_id"
    companies ||--o{ competitors : "competitor_id"
    
    sources ||--o{ source_states : "source_id"
    companies ||--o{ source_states : "company_id"

    companies ||--o{ documents : "company_id"
    sources ||--o{ documents : "source_id"

    documents ||--o{ document_versions : "document_id"

    documents ||--o{ document_topics : "document_id"
    topics ||--o{ document_topics : "topic_id"

    documents ||--o{ sentiment_results : "document_id"
    analysis_runs ||--o{ sentiment_results : "analysis_id"

    documents ||--o{ entities : "document_id"

    documents ||--o{ embeddings : "document_id"

    companies ||--o{ analysis_runs : "company_id"

    analysis_runs ||--o{ analysis_competitors : "analysis_run_id"
    companies ||--o{ analysis_competitors : "competitor_id"

    companies ||--o{ market_metrics : "company_id"
    analysis_runs ||--o{ market_metrics : "analysis_id"

    companies ||--o{ insights : "company_id"
    analysis_runs ||--o{ insights : "analysis_id"

    companies ||--o{ predictions : "company_id"
    model_versions ||--o{ predictions : "model_version_id"

    companies ||--o{ ingestion_runs : "company_id"
    sources ||--o{ ingestion_runs : "source_id"

    companies ||--o{ reviews : "company_id"
"""

def generate_kroki(text, format='png'):
    # Kroki encoding
    compressed = zlib.compress(text.encode('utf-8'))
    payload = base64.urlsafe_b64encode(compressed).decode('ascii')
    url = f"https://kroki.io/mermaid/{format}/{payload}"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

out_dir = r"c:\Users\ayaan\OneDrive\Desktop\AI POWERED COMPETETIVE INTELLIGENCE & MARKET TREND PREDICTION PLATFORM\backend"

png_data = generate_kroki(mermaid_code, 'png')
if png_data:
    with open(os.path.join(out_dir, "database_schema_diagram.png"), "wb") as f:
        f.write(png_data)
    print("PNG generated.")

svg_data = generate_kroki(mermaid_code, 'svg')
if svg_data:
    with open(os.path.join(out_dir, "database_schema_diagram.svg"), "wb") as f:
        f.write(svg_data)
    print("SVG generated.")
