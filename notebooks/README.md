# 📊 Healthcare Analytics Notebooks

This directory contains Jupyter notebooks for exploratory data analysis, visualization, and model development.

## 📋 Available Notebooks

### 🏥 [Healthcare_Occupancy_EDA.ipynb](./Healthcare_Occupancy_EDA.ipynb)
**Comprehensive Exploratory Data Analysis & Data Cleaning**

**Purpose**: Complete analysis of healthcare patient flow and bed occupancy data with data cleaning, validation, and insights generation.

**Key Features**:
- ✅ **Data Quality Assessment**: Missing values, duplicates, validation checks
- ✅ **Data Cleaning**: Type conversion, anomaly detection, outlier handling
- ✅ **Descriptive Analytics**: Ward capacity, occupancy trends, SLA analysis
- ✅ **Temporal Analysis**: Hourly/daily patterns, trend identification
- ✅ **Event Analysis**: Patient admission/discharge patterns
- ✅ **Visualization**: 15+ charts using matplotlib, seaborn, plotly
- ✅ **Insights Generation**: Automated recommendations and key findings

**Data Sources**:
- SQLite Database (`../data/raw/hospital.db`)
- JSON Events (`../data/raw/test_events.json`)

**Analysis Sections**:
1. Data Loading & Initial Exploration
2. Data Quality Assessment & Cleaning
3. Exploratory Data Analysis
4. Correlation & Pattern Analysis
5. Key Insights & Recommendations
6. Data Quality Summary

## 🚀 Getting Started

### Prerequisites
```bash
# Install dependencies
pip install -r ../requirements.txt
```

### Running the Notebooks
```bash
# Start Jupyter
jupyter notebook

# Or use Jupyter Lab
jupyter lab
```

### Data Path Configuration
The notebooks are configured to read data from:
- Raw data: `../data/raw/`
- Processed data: `../data/processed/`

## 📈 Key Metrics Analyzed

### Occupancy Metrics
- **Current Occupancy**: Real-time bed utilization
- **Historical Trends**: Hourly, daily, weekly patterns
- **Capacity Planning**: Total beds vs. occupied beds
- **SLA Compliance**: Breach detection and analysis

### Operational Metrics
- **Patient Flow**: Admission/discharge rates
- **Event Processing**: Real-time event analysis
- **Anomaly Detection**: Statistical outlier identification
- **Alert Generation**: Automated breach notifications

### Quality Metrics
- **Data Completeness**: Missing value analysis
- **Data Validation**: Range and consistency checks
- **Temporal Integrity**: Timestamp validation
- **Referential Integrity**: Relationship validation

## 🛠️ Tools & Libraries

- **Data Processing**: pandas, numpy, sqlite3
- **Visualization**: matplotlib, seaborn, plotly
- **Statistics**: scipy, statsmodels
- **Machine Learning**: scikit-learn
- **Utilities**: datetime, pathlib, warnings

## 📊 Output & Deliverables

### Visualizations
- Ward capacity overviews
- Occupancy trend lines
- SLA breach analysis
- Event distribution charts
- Correlation heatmaps
- Anomaly detection plots

### Reports
- Automated data quality summary
- Key insights and recommendations
- Performance metrics
- Operational alerts

### Export Options
- PDF reports via notebook export
- Interactive HTML dashboards
- CSV data extracts
- Image files for presentations

## 🔧 Customization

### Adding New Analysis
1. Create a new notebook in this directory
2. Follow the naming convention: `AnalysisName_Description.ipynb`
3. Update this README with your notebook details

### Data Source Updates
- Update data paths in notebook cells
- Modify SQL queries for new tables
- Adjust visualization parameters

## 📝 Notes

- **Performance**: Large datasets may require sampling
- **Memory**: Close database connections after use
- **Security**: Ensure sensitive data is properly masked
- **Version Control**: Notebooks are excluded from git by default

## 🤝 Contributing

When adding new notebooks:
1. Include comprehensive documentation
2. Add error handling and validation
3. Provide clear data source information
4. Update this README file

---

*For questions or support, refer to the main project README or contact the analytics team.*
