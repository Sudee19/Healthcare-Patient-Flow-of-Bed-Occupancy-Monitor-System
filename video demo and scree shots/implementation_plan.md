# Healthcare Patient Flow & Bed Occupancy Monitor — Implementation Plan

## Build Strategy

### ✅ What I Will Build Automatically
| Phase | Components |
|-------|-----------|
| Phase 0 | Architecture docs, data contracts, project structure |
| Phase 1 | HL7 event simulator, Kafka Docker setup, producer scripts |
| Phase 2 | PySpark Bronze/Silver/Gold layers, Z-score anomaly detection |
| Phase 3 | Airflow DAGs (hourly snapshot, daily report, SLA monitoring) |
| Phase 4 | LLM context assembler, prompt templates, API integration |
| Phase 5 | FastAPI backend with REST + WebSocket endpoints |
| Phase 6 | React dashboard with heatmap, gauges, alerts, charts |
| Phase 9 | 15 SQL business questions, Jupyter EDA notebook |
| Phase 10 | README, architecture diagrams (Mermaid), interview prep |

### 📋 What You Must Do Manually (Procedures Provided)
| Phase | Components | Reason |
|-------|-----------|--------|
| Phase 7 | Azure resources (ADLS, SQL, ADF) | Requires Azure subscription + portal login |
| Phase 8 | Databricks Community Edition | Requires account creation + cluster setup |
| Phase 9 | Power BI / Tableau dashboards | Requires desktop app + interactive design |
| Phase 10 | Demo video recording | Requires screen recording + narration |

---

## Architecture Overview

```
┌─────────────┐    ┌───────┐    ┌────────┐    ┌─────────┐    ┌─────────┐    ┌────────┐    ┌───────┐
│  Simulator   │───▶│ Kafka │───▶│ PySpark│───▶│ Storage │───▶│ Airflow │───▶│FastAPI │───▶│ React │
│ (Python)     │    │(Docker)│    │(Local) │    │(Parquet/│    │ (DAGs)  │    │  API   │    │ Dash  │
│              │    │        │    │        │    │ SQLite) │    │         │    │        │    │       │
└─────────────┘    └───────┘    └────────┘    └─────────┘    └─────────┘    └────────┘    └───────┘
                                                   │              │
                                                   ▼              ▼
                                              ┌─────────┐   ┌─────────┐
                                              │  Azure   │   │  LLM    │
                                              │ (ADLS/   │   │(Claude) │
                                              │  SQL/ADF)│   │         │
                                              └─────────┘   └─────────┘
                                                   │
                                                   ▼
                                              ┌──────────┐
                                              │Databricks│
                                              │ (Delta)  │
                                              └──────────┘
```

## Data Contract

### Event Structure (HL7-Style ADT Events)
```json
{
  "message_id": "uuid",
  "event_type": "ADT_A01 | ADT_A02 | ADT_A03",
  "patient_id": "P-XXXXXX",
  "ward_id": "W-XXX",
  "ward_name": "ICU East | ICU West | General A | General B | Pediatrics | Emergency | Oncology",
  "bed_id": "B-XXXX",
  "timestamp": "ISO 8601",
  "diagnosis_category": "cardiac | respiratory | trauma | ...",
  "transfer_from_ward": "W-XXX (only for ADT_A02)",
  "age_group": "pediatric | adult | geriatric",
  "priority": "emergency | elective | transfer"
}
```

### Ward Configuration
| Ward | ID | Beds | Normal Admits/hr | Spike Admits/hr |
|------|-----|------|-----------------|-----------------|
| ICU East | W-001 | 20 | 1–2 | 4–6 |
| ICU West | W-002 | 20 | 1–2 | 4–6 |
| General A | W-003 | 40 | 3–5 | 8–12 |
| General B | W-004 | 40 | 3–5 | 8–12 |
| Pediatrics | W-005 | 25 | 2–3 | 5–8 |
| Emergency | W-006 | 30 | 4–6 | 10–15 |
| Oncology | W-007 | 15 | 1–2 | 3–5 |
| **Total** | | **190** | | |

---

## Project Directory Structure
```
project-root/
├── docker-compose.yml           # Kafka + Zookeeper
├── requirements.txt             # Python dependencies
├── config/
│   └── wards.json              # Ward configuration
├── simulator/
│   ├── __init__.py
│   ├── event_generator.py      # HL7 event generator
│   ├── kafka_producer.py       # Kafka producer
│   └── config.py               # Simulator settings
├── spark/
│   ├── bronze_ingestion.py     # Raw event storage
│   ├── silver_cleaning.py      # Data quality rules
│   ├── gold_aggregation.py     # Occupancy calculations
│   └── anomaly_detection.py    # Z-score computation
├── airflow/
│   └── dags/
│       ├── hourly_snapshot.py
│       ├── daily_report.py
│       └── sla_monitoring.py
├── llm/
│   ├── context_assembler.py
│   ├── prompt_templates.py
│   └── llm_client.py
├── api/
│   ├── main.py                 # FastAPI app
│   ├── models.py               # Pydantic models
│   ├── routes/
│   │   ├── wards.py
│   │   ├── alerts.py
│   │   └── anomalies.py
│   └── websocket.py
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── WardGrid.jsx
│   │   │   ├── WardCard.jsx
│   │   │   ├── AlertFeed.jsx
│   │   │   ├── WardDetailModal.jsx
│   │   │   ├── AnomalyBanner.jsx
│   │   │   └── OccupancyGauge.jsx
│   │   └── styles/
│   ├── public/
│   └── index.html
├── analytics/
│   ├── sql_queries/             # 15 SQL business questions
│   └── eda_notebook.ipynb       # Jupyter EDA
├── azure/
│   ├── setup_guide.md           # Manual Azure setup instructions
│   ├── adf_pipelines/
│   └── sql_schema.sql
├── databricks/
│   ├── setup_guide.md
│   └── notebooks/
│       ├── 01_bronze_ingestion.py
│       ├── 02_silver_cleaning.py
│       ├── 03_gold_aggregation.py
│       └── 04_anomaly_detection.py
├── docs/
│   ├── architecture_local.md
│   ├── architecture_cloud.md
│   ├── data_lineage.md
│   └── interview_prep.md
└── README.md
```

---

## Build Order

| Step | Phase | What | Status |
|------|-------|------|--------|
| 1 | 0 | Project structure + data contracts | 🔲 |
| 2 | 1 | HL7 event simulator | 🔲 |
| 3 | 1 | Docker Compose (Kafka) | 🔲 |
| 4 | 1 | Kafka producer integration | 🔲 |
| 5 | 2 | PySpark Bronze layer | 🔲 |
| 6 | 2 | PySpark Silver layer | 🔲 |
| 7 | 2 | PySpark Gold layer | 🔲 |
| 8 | 2 | Z-score anomaly detection | 🔲 |
| 9 | 3 | Airflow DAGs (all 3) | 🔲 |
| 10 | 4 | LLM intelligence layer | 🔲 |
| 11 | 5 | FastAPI backend | 🔲 |
| 12 | 6 | React frontend | 🔲 |
| 13 | 7 | Azure setup guide + scripts | 🔲 |
| 14 | 8 | Databricks notebooks | 🔲 |
| 15 | 9 | SQL queries + EDA notebook | 🔲 |
| 16 | 10 | Documentation + README | 🔲 |
