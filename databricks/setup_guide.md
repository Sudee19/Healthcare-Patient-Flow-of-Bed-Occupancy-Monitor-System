# Databricks Setup Guide — Phase 8

## Step 1: Create Databricks Account

1. Go to [Databricks Community Edition](https://community.cloud.databricks.com/login.html)
2. Sign up with your email (free tier, no credit card needed)
3. After login, create a cluster:
   - Name: `hospital-monitor`
   - Runtime: `14.3 LTS` (includes Spark 3.5)
   - Node type: Community Edition default
   - Click "Create Cluster" and wait ~5 min for startup

## Step 2: Upload Data

1. In Databricks sidebar → **Data** → **Create Table**
2. Upload these files from your local `data/` folder:
   - `data/gold/occupancy_hourly/*.parquet`
   - `data/silver/*.parquet`
   - Or use the JSON test events file
3. Alternatively, mount your ADLS storage (see below)

### Mount ADLS (if you set up Azure):
```python
# Run in a notebook cell
dbutils.fs.mount(
  source = "wasbs://bronze@sthospitalmonitor.blob.core.windows.net",
  mount_point = "/mnt/hospital/bronze",
  extra_configs = {
    "fs.azure.account.key.sthospitalmonitor.blob.core.windows.net": "<YOUR_KEY>"
  }
)
```

## Step 3: Import Notebooks

1. Download the 4 notebooks from `databricks/notebooks/`
2. In Databricks sidebar → **Workspace** → **Import**
3. Upload all 4 notebooks
4. Attach them to your cluster

## Step 4: Run the Medallion Pipeline

Run notebooks in order:
1. `01_bronze_ingestion` — Reads raw events, writes to Delta
2. `02_silver_cleaning` — Applies quality rules
3. `03_gold_aggregation` — Occupancy calculations
4. `04_anomaly_detection` — Z-score computation

## Step 5: Create Workflow

1. **Workflows** → **Create Job**
2. Name: `Hospital Medallion Pipeline`
3. Add tasks in sequence: Bronze → Silver → Gold → Anomaly
4. Schedule: daily
5. Take screenshot of the workflow DAG

## Screenshot Checklist for Portfolio
- [ ] Cluster configuration page
- [ ] Notebook with Delta Lake table creation
- [ ] `DESCRIBE HISTORY` showing Delta time travel
- [ ] `OPTIMIZE` command output
- [ ] Spark UI showing job DAG
- [ ] Spark UI showing stage execution plan
- [ ] Workflow job runs (successful pipeline)
