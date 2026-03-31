# Healthcare Patient Flow & Bed Occupancy Monitor - Project Structure

## 📁 Project Organization

This project follows a clean, modular architecture designed for scalability and maintainability.

```
Healthcare Patient Flow of Bed Occupancy Monitor Project/
├── 📂 data/                          # Data storage
│   ├── 📂 raw/                      # Raw, unprocessed data
│   │   ├── hospital.db              # SQLite database with historical data
│   │   ├── test_events.json         # Patient admission/discharge events
│   │   └── test_events_ndjson.json  # NDJSON format events
│   └── 📂 processed/                # Cleaned and processed data
│
├── 📂 src/                          # Source code
│   ├── 📂 api/                      # API endpoints and services
│   ├── 📂 data_processing/          # Data ingestion and cleaning
│   │   ├── explore_data.py          # Data exploration utilities
│   │   └── seed_data.py             # Database seeding scripts
│   ├── 📂 analytics/                # Analytics and ML models
│   └── 📂 utils/                    # Common utilities and helpers
│
├── 📂 notebooks/                    # Jupyter notebooks for analysis
│   └── Healthcare_Occupancy_EDA.ipynb  # Comprehensive EDA notebook
│
├── 📂 scripts/                      # Execution and automation scripts
│   └── run_pipeline.py              # Main pipeline execution script
│
├── 📂 tests/                        # Test suites
│   ├── 📂 unit/                     # Unit tests
│   └── 📂 integration/              # Integration tests
│
├── 📂 docs/                         # Documentation
│   ├── 📂 technical/                # Technical documentation
│   └── 📂 user_guide/               # User guides and tutorials
│
├── 📂 config/                       # Configuration files
├── 📂 deployment/                   # Deployment configurations
├── 📂 monitoring/                   # Monitoring and logging setup
├── 📂 logs/                         # Application logs
│
├── 📂 analytics/                    # Analytics outputs and reports
│   ├── powerbi_tableau_guide.md     # BI tool integration guide
│   └── 📂 sql_queries/              # SQL query library
│
├── 📂 api/                          # API implementation (FastAPI)
├── 📂 airflow/                      # Airflow DAGs and configuration
├── 📂 azure/                        # Azure cloud configurations
├── 📂 databricks/                   # Databricks notebooks and jobs
├── 📂 db/                           # Database schemas and migrations
├── 📂 flask-dashboard/              # Flask-based dashboard
├── 📂 frontend/                     # React frontend application
├── 📂 llm/                          # LLM integration and prompts
├── 📂 react-dashboard/              # React dashboard implementation
├── 📂 simulator/                    # Data simulation tools
├── 📂 spark/                        # Spark jobs and configurations
├── 📂 webapp/                       # Web application components
│
├── 📄 .env.example                  # Environment variables template
├── 📄 .gitignore                    # Git ignore rules
├── 📄 README.md                     # Project overview and setup
├── 📄 requirements.txt              # Python dependencies
├── 📄 docker-compose.yml            # Docker services configuration
├── 📄 docker-compose-airflow.yml    # Airflow-specific Docker config
└── 📄 PROJECT_STRUCTURE.md          # This file
```

## 🗂️ Directory Descriptions

### `/data/`
- **`raw/`**: Contains original, unmodified data sources
- **`processed/`**: Cleaned, transformed, and analysis-ready data

### `/src/`
Core application source code organized by functionality:
- **`api/`**: REST API endpoints and business logic
- **`data_processing/`**: ETL pipelines, data cleaning, validation
- **`analytics/`**: Statistical analysis, ML models, anomaly detection
- **`utils/`**: Shared utilities, constants, helper functions

### `/notebooks/`
Jupyter notebooks for:
- Exploratory Data Analysis (EDA)
- Data visualization
- Model development and testing
- Ad-hoc analysis

### `/scripts/`
Automation and execution scripts:
- Pipeline orchestration
- Data loading and seeding
- Deployment scripts

### `/tests/`
Comprehensive test suite:
- **`unit/`**: Individual component tests
- **`integration/`**: End-to-end workflow tests

### `/docs/`
Project documentation:
- **`technical/`**: Architecture, API docs, deployment guides
- **`user_guide/`**: User manuals, tutorials, best practices

### `/config/`
Configuration files for different environments:
- Database connections
- API settings
- Monitoring thresholds

## 🔄 Data Flow

```
Raw Data → Data Processing → Analytics → Dashboard/Alerts
    ↓           ↓              ↓            ↓
  /data/raw → /src/data_processing → /src/analytics → /frontend/
```

## 🚀 Getting Started

1. **Setup Environment**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run EDA Analysis**:
   ```bash
   jupyter notebook notebooks/Healthcare_Occupancy_EDA.ipynb
   ```

3. **Start Pipeline**:
   ```bash
   python scripts/run_pipeline.py
   ```

## 📊 Key Components

- **Database**: SQLite with 10+ tables for occupancy tracking
- **Analytics**: Real-time monitoring, SLA breach detection, anomaly identification
- **Visualization**: Multiple dashboard options (React, Flask, PowerBI)
- **ML Integration**: LLM-powered explanations and predictions
- **Infrastructure**: Docker, Airflow, Spark, Azure support

## 🛠️ Development Guidelines

- Follow the existing directory structure
- Add new features to appropriate `/src/` subdirectories
- Include tests in `/tests/` directory
- Update documentation in `/docs/`
- Use `/notebooks/` for analysis and development

## 📈 Monitoring & Logging

- Application logs: `/logs/`
- Monitoring configs: `/monitoring/`
- Performance metrics: Integrated with dashboard

## 🔄 CI/CD

- Deployment configs: `/deployment/`
- Docker configurations: Root level docker-compose files
- Environment templates: `.env.example`

---

*This structure supports both development and production deployments while maintaining clear separation of concerns.*
