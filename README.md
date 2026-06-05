# Agentic DE Lifecycle - EDA Tool

Schema-Aware Exploratory Data Analysis tool for databases and file uploads. This is the first component of a broader agentic automation framework for the Data Engineering lifecycle.

## Features

### Dual Mode Support
- **Database Mode**: Analyze PostgreSQL/Greenplum tables with schema-aware insights
- **File Upload Mode**: Analyze Excel/CSV files with smart primary key detection

### Automated EDA Insights
- **Data Availability**: Freshness status, time distribution (fiscal quarters), growth trends
- **Column Classification**: Automatic categorization (ID/Key, Numeric, Date/Time, Text/Other)
- **Null Analysis**: Null percentage analysis for key columns
- **Top Values Analysis**: Most frequent values in categorical columns
- **Column Cardinality**: Unique value ratio analysis
- **Data Completeness**: Overall completeness score across columns
- **Schema Preview**: Column structure and data types

### Smart Features
- **Primary Key Detection**: Auto-detects PK from naming patterns or database constraints
- **Column Prioritization**: Analyzes important columns first (PK, FK, indexed, date columns)
- **Fiscal Calendar**: Q1=Feb-Apr, Q2=May-Jul, Q3=Aug-Oct, Q4=Nov-Jan
- **Performance Optimization**: Smart sampling for wide tables

## Installation

```bash
pip install -r requirements_file.txt
```

For database mode, also install:
```bash
pip install psycopg2-binary
```

## Usage

### Run Unified App (Both Modes)
```bash
streamlit run app_unified.py
```

### Run File Upload Only
```bash
streamlit run app_file.py
```

### Run Database Only
```bash
streamlit run app.py
```

## Deployment

This app can be deployed to Streamlit Cloud for free:
1. Push this repository to GitHub/GitLab
2. Connect to [Streamlit Cloud](https://share.streamlit.io)
3. Configure secrets for database credentials (if using DB mode)

## Roadmap

This EDA tool is the foundation for a broader agentic DE lifecycle automation framework. Future phases will include:
- Graph-based relationship visualization
- Automated data quality monitoring
- Intelligent data lineage tracking
- Autonomous ETL pipeline generation

## Files

- `app_unified.py` - Unified app with both DB and file modes
- `app_file.py` - File upload only version
- `app.py` - Database only version
- `eda_engine.py` - Database EDA engine
- `eda_engine_file.py` - File EDA engine
- `requirements_file.txt` - Dependencies
- `sample_orders.xlsx` - Sample data for testing
