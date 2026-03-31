# 🏥 Healthcare Patient Flow & Bed Occupancy Monitor

A comprehensive data engineering and analytics platform that monitors hospital bed occupancy in real time, detects anomalous admission patterns, and generates AI-powered explanations for SLA breaches.

> **Portfolio project** demonstrating: Kafka streaming, PySpark medallion architecture, Airflow orchestration, LLM integration, FastAPI, React dashboard, Azure cloud deployment, and Databricks.

---

## � **Project Overview**

This system provides **real-time monitoring** of hospital bed occupancy across multiple wards, with **automated SLA breach detection**, **anomaly detection**, and **comprehensive analytics** for healthcare operations optimization.

### 📊 **Key Features**
- 🔴 **Real-time Occupancy Monitoring** across 7 hospital wards (190 beds)
- ⚠️ **SLA Breach Detection** with automated alerts (85% threshold)
- 🚨 **Anomaly Detection** using statistical methods (Z-score analysis)
- 📈 **Comprehensive Analytics** with 15+ visualizations
- 🤖 **AI-Powered Insights** with LLM explanations for operational decisions
- 📱 **Multi-dashboard Support** (React, Flask, PowerBI integration)

---

## �🏗️ **Architecture**

### Local Development Stack
```
Simulator (Python) → Kafka (Docker) → PySpark (Local) → SQLite → Airflow → FastAPI → React
                                                                      ↓
                                                                 Claude LLM
```

### Cloud Production Stack
```
Azure Functions → Azure Kafka → Databricks → Azure SQL → Airflow (Azure) → FastAPI (Azure) → React
                                                                                ↓
                                                                           Claude LLM
```

---

## 📋 **What's Included**

### 📊 **Data Analytics & EDA**
- ✅ **Complete EDA Notebook** (`notebooks/Healthcare_Occupancy_EDA.ipynb`)
- ✅ **Data Quality Assessment** with validation and cleaning
- ✅ **Ward Capacity Analysis** with current status monitoring
- ✅ **Temporal Analysis** (hourly/daily patterns)
- ✅ **SLA Breach Analysis** with duration tracking
- ✅ **Event Pattern Analysis** (10,047 patient events)
- ✅ **Anomaly Detection** (2,955 statistical checks)

### 🏗️ **Project Structure**
```
├── 📂 data/                    # Data storage
│   ├── 📂 raw/                 # Original data sources
│   └── 📂 processed/           # Cleaned data outputs
├── 📂 src/                     # Source code
│   ├── 📂 api/                 # API endpoints
│   ├── 📂 data_processing/     # ETL pipelines
│   ├── 📂 analytics/           # Analytics & ML models
│   └── 📂 utils/               # Common utilities
├── 📂 notebooks/               # Jupyter analysis notebooks
├── 📂 scripts/                 # Automation scripts
├── 📂 tests/                   # Test suites
├── 📂 docs/                    # Documentation
├── 📂 frontend/                # React dashboard
├── 📂 api/                     # FastAPI backend
├── 📂 airflow/                 # Airflow DAGs
├── 📂 spark/                   # Spark jobs
└── 📂 azure/                   # Cloud deployment
```

### 📚 **Documentation**
- 📖 **Complete Technical Guide** (`docs/Healthcare_Project_Complete_Guide.md`)
- 📋 **Executive Summary** (`docs/Executive_Summary.md`)
- 🔧 **API Documentation** (`docs/api/`)
- 📊 **Analytics Guide** (`docs/analytics/`)

---

## 🚀 **Quick Start**

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Node.js 16+
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Sudee19/healthcare-patient-flow-monitor.git
cd healthcare-patient-flow-monitor
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Start infrastructure**
```bash
# Start Kafka and other services
docker-compose up -d

# Start Airflow
docker-compose -f docker-compose-airflow.yml up -d
```

4. **Run the analysis**
```bash
# Run EDA demo
python run_eda_demo.py

# Create visualizations
python create_visualizations.py
```

5. **Start the dashboard**
```bash
# React dashboard
cd frontend && npm install && npm start

# Or Flask dashboard
cd flask-dashboard && python app.py
```

---

## 📊 **Current System Status**

### 🏥 **Ward Occupancy Status**
```
🟢 ICU East:     0/20 beds (0.0%)   - normal
🟢 ICU West:     0/20 beds (0.0%)   - normal  
🔴 General A:    40/40 beds (100.0%) - CRITICAL
🔴 General B:    40/40 beds (100.0%) - CRITICAL
🟢 Pediatrics:   0/25 beds (0.0%)   - normal
🔴 Emergency:    30/30 beds (100.0%) - CRITICAL
🟢 Oncology:     0/15 beds (0.0%)   - normal
```

### 📈 **Key Metrics**
- **190 Total Beds** across 7 wards
- **42.9% Average Occupancy** rate
- **3 Critical Wards** at 100% capacity
- **8 Active SLA Breaches** requiring attention
- **10,047 Patient Events** processed
- **2,955 Anomaly Checks** performed

---

## 🛠️ **Technology Stack**

### **Backend**
- **Python 3.11**: Primary programming language
- **FastAPI**: REST API framework
- **SQLite**: Local database
- **SQLAlchemy**: Database ORM
- **Pandas & NumPy**: Data processing

### **Data Engineering**
- **Apache Kafka**: Event streaming
- **PySpark**: Big data processing
- **Apache Airflow**: Workflow orchestration
- **Docker**: Containerization

### **Analytics & ML**
- **Scikit-learn**: Machine learning
- **Statsmodels**: Statistical analysis
- **Matplotlib & Seaborn**: Data visualization
- **Plotly**: Interactive charts

### **Frontend**
- **React 18**: Modern UI framework
- **TypeScript**: Type-safe JavaScript
- **TailwindCSS**: Styling
- **Chart.js**: Data visualization

### **AI & Cloud**
- **Claude LLM**: AI-powered explanations
- **Azure**: Cloud deployment
- **Databricks**: Big data analytics

---

## 📊 **Analytics & Insights**

### **Exploratory Data Analysis**
The comprehensive EDA covers:

1. **Data Quality Assessment**
   - Missing value analysis
   - Duplicate detection
   - Range validation

2. **Ward Capacity Analysis**
   - Current occupancy monitoring
   - Critical ward identification
   - SLA threshold tracking

3. **Temporal Analysis**
   - Hourly occupancy patterns
   - Daily trend analysis
   - Peak period identification

4. **Event Pattern Analysis**
   - Admission/discharge patterns
   - Priority distribution
   - Diagnosis category analysis

5. **Anomaly Detection**
   - Statistical outlier detection
   - Z-score analysis
   - Baseline monitoring

### **Key Insights**
- **Immediate Actions**: Address critical occupancy in General A, General B, Emergency
- **Operational Improvements**: Implement predictive scheduling, enhance discharge planning
- **Monitoring Enhancements**: Add real-time alerts, implement trend-based predictions

---

## 🔧 **API Endpoints**

### **Occupancy Monitoring**
```python
GET /api/v1/occupancy/current          # Current occupancy status
GET /api/v1/occupancy/history         # Historical occupancy data
GET /api/v1/occupancy/wards/{ward_id} # Ward-specific data
```

### **SLA Management**
```python
GET /api/v1/sla/breaches              # Active SLA breaches
GET /api/v1/sla/history               # Historical breaches
POST /api/v1/sla/resolve              # Mark breach as resolved
```

### **Analytics**
```python
GET /api/v1/analytics/summary         # Executive summary
GET /api/v1/analytics/trends          # Trend analysis
GET /api/v1/analytics/anomalies       # Anomaly detection results
```

---

## 🚀 **Deployment**

### **Local Development**
```bash
# Start all services
docker-compose up -d

# Run data pipeline
python scripts/run_pipeline.py

# Start API server
uvicorn api.main:app --reload
```

### **Azure Cloud Deployment**
```bash
# Deploy to Azure
az group create --name healthcare-rg --location eastus
az deployment group create --resource-group healthcare-rg --template-file deployment/azure-template.json
```

### **Environment Variables**
```bash
# Database
DATABASE_URL=sqlite:///./data/hospital.db

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# LLM
ANTHROPIC_API_KEY=your_api_key_here

# Azure
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
```

---

## 📊 **Monitoring & Alerting**

### **SLA Monitoring**
- **Threshold**: 85% occupancy triggers alert
- **Escalation**: 2+ hours = high priority
- **Notification**: Email, Slack, SMS

### **Anomaly Detection**
- **Method**: Z-score > 2.5
- **Frequency**: Hourly checks
- **Baseline**: 7-day rolling average

### **System Health**
- **Uptime**: 99.9% availability target
- **Latency**: <100ms API response time
- **Data Freshness**: <5 minute delay

---

## 🧪 **Testing**

### **Run Tests**
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# Coverage report
pytest --cov=src tests/
```

### **Test Coverage**
- **Unit Tests**: 85%+ coverage target
- **Integration Tests**: API endpoints and data pipelines
- **E2E Tests**: Complete user workflows

---

## 📚 **Documentation**

### **Complete Documentation Package**
- 📖 **[Technical Guide](docs/Healthcare_Project_Complete_Guide.md)** - Complete implementation details
- 📋 **[Executive Summary](docs/Executive_Summary.md)** - Business overview and impact
- 🔧 **[API Documentation](docs/api/)** - REST API reference
- 📊 **[Analytics Guide](docs/analytics/)** - Data analysis documentation

### **Interactive Documentation**
- **Jupyter Notebooks**: `notebooks/Healthcare_Occupancy_EDA.ipynb`
- **HTML Documentation**: Open `Healthcare_Project_Complete_Guide.html`
- **API Docs**: Visit `/docs` when API is running

---

## 🎥 Live Demo

### 📹 **Video Demonstrations**

#### 🏥 Healthcare Patient Flow Monitor Web App
![Healthcare Monitor Demo](https://github.com/Sudee19/Healthcare-Patient-Flow-of-Bed-Occupancy-Monitor-system/releases/download/v1.0-demo/Healthcare%20Patient%20Flow%20of%20Bed%20Occupancy%20Monitor%20web%20app%20demo)

**🎥 [Click here to watch the healthcare monitoring dashboard in action](https://github.com/Sudee19/Healthcare-Patient-Flow-of-Bed-Occupancy-Monitor-system/releases/download/v1.0-demo/Healthcare%20Patient%20Flow%20of%20Bed%20Occupancy%20Monitor%20web%20app%20demo)**

*Features demonstrated: Real-time occupancy monitoring, SLA breach detection, anomaly detection, AI-powered analytics*

#### 🔄 Airflow Workflow Management Demo
![Airflow Demo](https://github.com/Sudee19/Healthcare-Patient-Flow-of-Bed-Occupancy-Monitor-system/releases/download/v1.0-demo/Airflow%20demo)

**🔄 [Click here to watch Airflow workflow automation in action](https://github.com/Sudee19/Healthcare-Patient-Flow-of-Bed-Occupancy-Monitor-system/releases/download/v1.0-demo/Airflow%20demo)**

*Features demonstrated: Automated data pipelines, SLA breach monitoring, workflow orchestration*

---

### 📋 **How to View Videos:**

1. **Click the video images above** - they will open the video in your browser
2. **Or click the text links** - direct download and playback
3. **Videos are hosted on GitHub** - no external hosting needed
4. **Works on all devices** - desktop, mobile, tablet

---

### 🎯 **Project Impact:**
- **190 hospital beds** monitored in real-time
- **3 critical wards** identified requiring attention
- **8 SLA breaches** detected and tracked
- **10,047 patient events** processed and analyzed
- **2,955 anomaly checks** performed

### 🚀 **Features Showcased:**
- 🔴 **Real-time Occupancy Monitoring** across 7 hospital wards
- ⚠️ **SLA Breach Detection** with automated alerts
- 🚨 **Anomaly Detection** using statistical methods
- 📈 **Interactive Dashboards** with live updates
- 🤖️ **AI-Powered Insights** with Claude LLM integration
- 🔄 **Workflow Automation** with Apache Airflow

### 🛠️ **Technology Stack:**
- **Backend**: Python, FastAPI, SQLite, SQLAlchemy
- **Data Engineering**: Kafka, PySpark, Apache Airflow
- **Big Data**: Databricks, Azure Cloud
- **Frontend**: React 18, TypeScript, TailwindCSS
- **AI/ML**: Claude LLM, Scikit-learn, Statsmodels

### 📊 **Project Impact:**
- **190 hospital beds** monitored in real-time
- **3 critical wards** identified requiring attention
- **8 SLA breaches** detected and tracked
- **10,047 patient events** processed and analyzed
- **2,955 anomaly checks** performed

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Development Guidelines**
- Follow PEP 8 for Python code
- Use TypeScript for frontend
- Add tests for new features
- Update documentation

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🏆 **Acknowledgments**

- **Healthcare Data Providers** for the realistic dataset
- **Apache Kafka** for reliable event streaming
- **Databricks** for big data analytics platform
- **Claude (Anthropic)** for AI-powered insights
- **Azure** for cloud infrastructure support

---

## 📞 **Contact**

- **GitHub**: [@Sudee19](https://github.com/Sudee19)
- **Portfolio**: [Link to portfolio]
- **Email**: [Your email]

---

## 🎯 **Project Impact**

### **Operational Excellence**
- **Improved Decision Making**: Data-driven operational planning
- **Enhanced Patient Care**: Better resource allocation and flow
- **Risk Mitigation**: Proactive capacity management
- **Cost Optimization**: Efficient staffing and resource utilization

### **Technical Innovation**
- **Real-time Analytics**: Sub-minute data processing
- **AI Integration**: LLM-powered operational insights
- **Scalable Architecture**: Cloud-ready microservices
- **Modern Tech Stack**: Industry-leading tools and frameworks

### **Business Value**
- **ROI**: Improved operational efficiency and patient outcomes
- **Scalability**: Multi-hospital deployment capability
- **Competitive Advantage**: Advanced analytics and AI capabilities
- **Future-Proof**: Foundation for continued innovation

---

*🏥 **Transforming Healthcare Operations Through Data Analytics and AI** 🚀*
```

### Cloud Stack
```
ADLS Gen2 (Bronze/Silver/Gold) → Azure Data Factory → Azure SQL → Power BI
                    ↓
              Databricks (Delta Lake, OPTIMIZE, ZORDER, Time Travel)
```

---

## 📂 Project Structure

```
├── simulator/          # HL7 ADT event generator with Kafka producer
├── spark/              # PySpark Bronze → Silver → Gold medallion pipeline
├── airflow/dags/       # 3 DAGs: hourly snapshot, daily report, SLA monitoring
├── llm/                # Claude API integration with fallback
├── api/                # FastAPI REST + WebSocket endpoints
├── frontend/           # React dashboard with real-time updates
├── analytics/          # 15 SQL business questions + EDA notebook
├── azure/              # Azure setup guide + SQL schema
├── databricks/         # 4 Delta Lake notebooks
├── config/             # Ward definitions and thresholds
├── docs/               # Architecture diagrams + interview prep
└── docker-compose.yml  # Kafka + Zookeeper
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- Docker Desktop
- Python 3.10+
- Java 11 (for Spark)
- Node.js 18+

### 1. Start Kafka
```bash
docker-compose up -d
```

### 2. Install Python Dependencies
```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 3. Initialize Database
```bash
python -c "from db import init_database; init_database()"
```

### 4. Generate Test Data
```bash
python -m simulator.run_simulator --mode batch --hours 168 --events-per-hour 60 --output ./data/test_events.json
```

### 5. Run Spark Pipeline
```bash
# Bronze
python spark/bronze_ingestion.py --mode json --input ./data/test_events.json

# Silver
python spark/silver_cleaning.py

# Gold
python spark/gold_aggregation.py

# Anomaly Detection
python spark/anomaly_detection.py
```

### 6. Start API Server
```bash
python -m api.main
# → http://localhost:8000/docs (Swagger UI)
```

### 7. Start React Dashboard
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 8. Run Live Simulator (Optional)
```bash
# Normal mode
python -m simulator.run_simulator --mode realtime --duration 30

# Outbreak mode (spike Emergency ward)
python -m simulator.run_simulator --mode realtime --duration 30 --outbreak --outbreak-ward W-006
```

---

## 📊 Data Engineering (DE) Highlights

### Medallion Architecture

```mermaid
flowchart LR
    subgraph Data Generation
      K([Kafka Topic / Simulator\nHospital ADT Events])
    end

    subgraph Bronze Layer "🥉 Bronze Layer (Raw)"
      B[(Parquet Data)]
      K -- spark/bronze_ingestion.py --> B
    end

    subgraph Silver Layer "🥈 Silver Layer (Cleaned)"
      S[(Parquet Data)]
      B -- spark/silver_cleaning.py --> S
    end

    subgraph Gold Layer "🥇 Gold Layer (Aggregated)"
      G1[(Parquet Analytics)]
      G2[(SQLite hospital.db)]
      S -- spark/gold_aggregation.py --> G1
      G1 -- Load to DB --> G2
    end
    
    subgraph Intelligence "🧠 Intelligence Layer"
      A(spark/anomaly_detection.py)
      A -- Z-Score Analytics --> G2
    end

    subgraph Presentation "🖥️ Dashboards & APIs"
      API(FastAPI)
      React(React Web App)
      G2 -- Query --> API
      API -- Websockets & REST --> React
    end
```

| Layer | Format | Purpose |
|-------|--------|---------|
| Bronze | Parquet (partitioned) | Raw, unmodified HL7 events |
| Silver | Parquet (partitioned) | Cleaned, validated, deduplicated |
| Gold | Parquet + SQLite | Aggregated occupancy metrics |

### Data Quality Rules (Silver)
1. Reject null `patient_id`
2. Reject invalid `event_type` (only ADT_A01/A02/A03)
3. Flag late arrivals (>24 hours old)
4. Standardize ward names
5. Deduplicate simultaneous admissions

### Airflow DAGs
| DAG | Schedule | Purpose |
|-----|----------|---------|
| `hourly_snapshot` | Every hour | Occupancy snapshot + SLA check |
| `daily_report` | Daily 6 AM | Aggregation + anomaly detection |
| `sla_monitoring` | Every 15 min | Consecutive breach tracking |

### Anomaly Detection
- Rolling 7-day mean/std per ward per hour-of-day
- Z-score computation with configurable threshold (default: 2.5)
- Outbreak detection signal for clinical operations

---

## 📈 Data Analytics (DA) Highlights

### 15 SQL Business Questions
Ranging from simple (`highest average occupancy`) to complex (`consecutive breach streaks using CTEs`) to window functions (`volatility ranking`, `percentile distribution`).

### Key Metrics
- **SLA Threshold**: 85% occupancy
- **Breach Window**: 2+ consecutive hours above threshold
- **Anomaly Threshold**: Z-score > 2.5

---

## 🤖 LLM Intelligence Layer

- **Purpose**: Generate plain-English explanations of occupancy alerts
- **Model**: Claude (with rule-based fallback)
- **Rate Limiting**: One API call per ward per breach event
- **Prompt Design**: Structured context injection with current stats, baseline, and trend
- **Fallback**: Template-based explanations ensure 100% coverage

---

## ☁️ Cloud Deployment

### Azure Resources
- **ADLS Gen2**: Bronze/Silver/Gold containers
- **Azure SQL**: Analytics layer (stored procedures, indexes)
- **Azure Data Factory**: 3 pipelines (ingest, transform, load)

### Databricks
- **Delta Lake**: ACID transactions, time travel, schema enforcement
- **OPTIMIZE + ZORDER**: Query performance on ward_id + timestamp
- **AutoLoader**: Incremental file ingestion
- **Workflow**: Scheduled medallion pipeline

> See `azure/setup_guide.md` and `databricks/setup_guide.md` for step-by-step instructions.

---

## 🖥️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/wards` | All wards with current status |
| GET | `/wards/{id}/history` | Hourly occupancy (past 24h) |
| GET | `/wards/{id}/baseline` | 7-day average baseline |
| GET | `/alerts/active` | Current SLA breaches + LLM explanations |
| GET | `/alerts/history` | Resolved breaches (past 7 days) |
| GET | `/anomalies` | Z-score flags |
| GET | `/dashboard/summary` | Combined dashboard data |
| WS | `/ws/alerts` | Real-time alert stream |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Event Simulation | Python, Faker |
| Message Broker | Apache Kafka (Docker) |
| Stream Processing | PySpark Structured Streaming |
| Orchestration | Apache Airflow |
| Storage | Parquet, SQLite, Delta Lake |
| LLM | Anthropic Claude API |
| Backend API | FastAPI + WebSocket |
| Frontend | React, Recharts, Vite |
| Cloud | Azure ADLS Gen2, Azure SQL, ADF |
| Big Data | Databricks (Delta Lake) |
| Analytics | SQL, Jupyter, Power BI |

---

## 📋 Ward Configuration

| Ward | Beds | SLA Status Colors |
|------|------|-------------------|
| ICU East | 20 | 🟢 Normal (<70%) |
| ICU West | 20 | 🟡 Elevated (70-85%) |
| General A | 40 | 🟠 Warning (85-95%) |
| General B | 40 | 🔴 Critical (>95%) |
| Pediatrics | 25 | |
| Emergency | 30 | |
| Oncology | 15 | |

---

## 📄 License

This project is for educational and portfolio purposes.
