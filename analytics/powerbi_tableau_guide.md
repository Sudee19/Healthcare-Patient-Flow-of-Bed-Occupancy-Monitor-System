# Power BI / Tableau Dashboard Guide — Phase 9

## Power BI Setup

### Step 1: Connect to Azure SQL
1. Open Power BI Desktop
2. Get Data → Azure → Azure SQL Database
3. Server: `sql-hospital-monitor.database.windows.net`
4. Database: `db-hospital`
5. Use DirectQuery mode for live data

### Step 2: Import Tables
Import these tables:
- `ward_occupancy_hourly`
- `ward_occupancy_daily`
- `ward_baseline`
- `sla_breaches`
- `anomaly_flags`
- `wards`

### Step 3: Create Relationships
```
wards.ward_id → ward_occupancy_hourly.ward_id (1:many)
wards.ward_id → ward_occupancy_daily.ward_id (1:many)
wards.ward_id → sla_breaches.ward_id (1:many)
wards.ward_id → anomaly_flags.ward_id (1:many)
```

### Step 4: Build 3 Dashboards

#### Dashboard 1: Operational View
- **Card visuals**: Total beds, Occupied, Available, Wards in breach
- **Matrix heatmap**: Ward × Hour → Occupancy % (conditional formatting green→red)
- **Bar chart**: Current occupancy per ward
- **Table**: Active SLA breaches with LLM explanations

#### Dashboard 2: Historical Trends
- **Line chart**: 30-day occupancy trend per ward (with 85% reference line)
- **Stacked bar**: Daily admits vs discharges per ward
- **KPI card**: SLA breach frequency this month vs last month
- **Small multiples**: One mini-chart per ward

#### Dashboard 3: Anomaly Report
- **Scatter plot**: Z-score vs admission count (color by is_anomaly)
- **Timeline**: Anomaly events over time
- **Table**: Top 10 anomalies with details
- **Card**: Total anomalies detected this week

### Step 5: Add Interactivity
- **Date slicer**: Filter by custom date range
- **Ward filter**: Dropdown for individual ward selection
- **Drill-through**: Click ward → see detailed hourly breakdown
- **Bookmarks**: Quick switch between Operational / Historical / Anomaly views

### Step 6: Export
- File → Export to PDF
- Take screenshots of each dashboard page
- Save .pbix file to the project repository

---

## Alternative: Tableau

### Connect to Data
1. Connect → Microsoft SQL Server
2. Enter Azure SQL credentials
3. Drag tables to canvas

### Sheets to Create
1. **Occupancy Heatmap**: Rows=Ward, Columns=Hour, Color=Occupancy%
2. **Trend Lines**: Date on X, Occupancy% on Y, Ward on Color
3. **Breach Timeline**: Gantt chart with breach start/end times
4. **Anomaly Scatter**: Z-score vs Count, sized by severity

### Dashboard Assembly
- Combine sheets into 3 dashboards matching Power BI layout
- Add filter actions for ward and date
- Export to Tableau Public for free hosting

---

## Screenshot Checklist for Portfolio
- [ ] Dashboard 1: Operational heatmap with active alerts
- [ ] Dashboard 2: 30-day trend with SLA line
- [ ] Dashboard 3: Anomaly timeline
- [ ] Date slicer in action
- [ ] Ward drill-through detail
