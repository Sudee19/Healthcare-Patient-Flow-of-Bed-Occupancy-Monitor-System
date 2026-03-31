# Azure Cloud Setup Guide — Phase 7

## Prerequisites
- Azure account with active subscription
- Azure CLI installed (`az --version`)
- Logged in via `az login`

---

## Step 1: Create Resource Group

```bash
az group create \
  --name rg-hospital-monitor \
  --location eastus
```

## Step 2: Create Azure Data Lake Storage Gen2

```bash
# Create storage account with hierarchical namespace (ADLS Gen2)
az storage account create \
  --name sthospitalmonitor \
  --resource-group rg-hospital-monitor \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2 \
  --hns true

# Get the storage account key
az storage account keys list \
  --account-name sthospitalmonitor \
  --resource-group rg-hospital-monitor \
  --query "[0].value" -o tsv

# Create containers (medallion architecture)
az storage container create --name bronze --account-name sthospitalmonitor
az storage container create --name silver --account-name sthospitalmonitor
az storage container create --name gold --account-name sthospitalmonitor
```

## Step 3: Create Azure SQL Database

```bash
# Create SQL Server
az sql server create \
  --name sql-hospital-monitor \
  --resource-group rg-hospital-monitor \
  --location eastus \
  --admin-user hospitaladmin \
  --admin-password "YourStrongPassword123!"

# Create database (Basic tier for portfolio)
az sql db create \
  --resource-group rg-hospital-monitor \
  --server sql-hospital-monitor \
  --name db-hospital \
  --service-objective Basic \
  --max-size 2GB

# Allow Azure services to connect
az sql server firewall-rule create \
  --resource-group rg-hospital-monitor \
  --server sql-hospital-monitor \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Allow your IP
az sql server firewall-rule create \
  --resource-group rg-hospital-monitor \
  --server sql-hospital-monitor \
  --name AllowMyIP \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

## Step 4: Create Azure Data Factory

```bash
az datafactory create \
  --resource-group rg-hospital-monitor \
  --factory-name adf-hospital-monitor \
  --location eastus
```

## Step 5: Set Up Azure SQL Schema

Connect to Azure SQL using Azure Data Studio or SSMS and run:

```sql
-- See azure/sql_schema.sql for the full schema
```

---

## ADF Pipeline Setup (Portal)

### Pipeline 1: Bronze Ingestion
1. Open ADF Studio → Author → New Pipeline
2. Add **Copy Data** activity
3. Source: ADLS Gen2 linked service → bronze container → Parquet format
4. Sink: Azure SQL → `ward_events_bronze` table
5. Trigger: **Tumbling window** (every hour)

### Pipeline 2: Silver Transformation
1. Add **Data Flow** activity
2. Source: ADLS bronze → Apply quality rules matching `silver_cleaning.py`
3. Sink: ADLS silver container
4. Trigger: **Blob event trigger** on bronze container

### Pipeline 3: Gold to SQL
1. Add **Copy Data** activity
2. Source: ADLS gold container → Parquet files
3. Sink: Azure SQL → `ward_occupancy_hourly`, `ward_baseline`, etc.
4. Trigger: **Daily at 7 AM**

### Screenshot Checklist for Portfolio
- [ ] Resource group overview (shows all resources)
- [ ] ADLS container structure (bronze/silver/gold)
- [ ] ADF pipeline diagram view
- [ ] ADF pipeline monitoring dashboard (successful runs)
- [ ] Azure SQL query editor showing data
