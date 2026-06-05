"""
Schema-Aware EDA Tool - Unified Version
Supports both Database (PostgreSQL/Greenplum) and File Upload (Excel/CSV)
"""

import streamlit as st
import pandas as pd
from eda_engine import run_full_eda
from eda_engine_file import run_full_eda_file
import psycopg2


# Page configuration
st.set_page_config(
    page_title="Schema-Aware EDA Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .mode-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .mode-card:hover {
        border-color: #667eea;
        transform: translateY(-2px);
    }
    .mode-card.selected {
        border-color: #667eea;
        background: #e8eaf6;
    }
</style>
""", unsafe_allow_html=True)


# Header
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-size: 2.5rem;">📊 Schema-Aware EDA Tool</h1>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Automated exploratory data analysis for databases and files</p>
</div>
""", unsafe_allow_html=True)


# Initialize session state
if 'mode' not in st.session_state:
    st.session_state.mode = None
if 'report' not in st.session_state:
    st.session_state.report = None
if 'df' not in st.session_state:
    st.session_state.df = None


# Mode Selection
if st.session_state.mode is None:
    st.subheader("🎯 Select Analysis Mode")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        if st.button("🗄️ Database Mode", use_container_width=True, key="db_mode"):
            st.session_state.mode = 'database'
            st.rerun()
    
    with col2:
        if st.button("📁 File Upload Mode", use_container_width=True, key="file_mode"):
            st.session_state.mode = 'file'
            st.rerun()
    
    st.info("Select a mode to begin analysis")
    st.stop()


# Database Mode
if st.session_state.mode == 'database':
    st.sidebar.header("🗄️ Database Connection")
    
    # Connection inputs
    host = st.sidebar.text_input("Host", value="localhost")
    port = st.sidebar.text_input("Port", value="5432")
    database = st.sidebar.text_input("Database", value="postgres")
    user = st.sidebar.text_input("User", value="postgres")
    password = st.sidebar.text_input("Password", type="password")
    
    # Table selection
    table_name = st.sidebar.text_input("Table Name", help="Enter the table name to analyze")
    
    # Analyze button
    if st.sidebar.button("🔍 Analyze Table", use_container_width=True):
        if not all([host, port, database, user, table_name]):
            st.sidebar.error("Please fill in all required fields")
        else:
            db_config = {
                'host': host,
                'port': int(port),
                'database': database,
                'user': user,
                'password': password
            }
            
            try:
                with st.spinner("Running EDA analysis..."):
                    report = run_full_eda(table_name, db_config)
                
                st.session_state.report = report
                st.success("✅ Analysis complete!")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Back button
    if st.sidebar.button("⬅️ Change Mode"):
        st.session_state.mode = None
        st.session_state.report = None
        st.rerun()


# File Upload Mode
if st.session_state.mode == 'file':
    st.sidebar.header("📁 File Upload")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload Excel or CSV file",
        type=['csv', 'xlsx', 'xls'],
        help="Supported formats: CSV, Excel (.xlsx, .xls)"
    )
    
    if uploaded_file:
        # Detect file type
        file_name = uploaded_file.name
        file_type = None
        
        if file_name.endswith('.csv'):
            file_type = 'csv'
        elif file_name.endswith(('.xlsx', '.xls')):
            file_type = 'excel'
        
        st.sidebar.success(f"✅ File uploaded: {file_name}")
        st.sidebar.info(f"Type: {file_type.upper()}")
        
        # Load file
        try:
            if file_type == 'csv':
                df = pd.read_csv(uploaded_file)
            elif file_type == 'excel':
                df = pd.read_excel(uploaded_file)
            
            st.sidebar.info(f"Rows: {len(df):,} | Columns: {len(df.columns)}")
            
            # Primary key selection
            st.sidebar.subheader("🔑 Primary Key Selection")
            pk_options = ['Auto-detect'] + list(df.columns)
            selected_pk = st.sidebar.selectbox(
                "Select primary key column",
                pk_options,
                index=0,
                help="Choose 'Auto-detect' to let the tool find the best candidate, or select manually"
            )
            
            primary_key = None if selected_pk == 'Auto-detect' else selected_pk
            
            # Analyze button
            if st.sidebar.button("🔍 Analyze File", use_container_width=True):
                with st.spinner("Running EDA analysis..."):
                    report = run_full_eda_file(df, file_name, primary_key)
                
                st.session_state.report = report
                st.session_state.df = df
                st.success("✅ Analysis complete!")
            
        except Exception as e:
            st.sidebar.error(f"Error loading file: {str(e)}")
    
    # Back button
    if st.sidebar.button("⬅️ Change Mode"):
        st.session_state.mode = None
        st.session_state.report = None
        st.session_state.df = None
        st.rerun()


# Display report if available
if st.session_state.report is not None:
    report = st.session_state.report
    
    # Row 1: Large header with table/file info
    if st.session_state.mode == 'database':
        st.markdown(f"""
        <div class="main-header" style="padding: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.8rem;">🗄️ {report['table_name']}</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                {report['row_count']:,} rows × {len(report['schema_df'])} columns
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="main-header" style="padding: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.8rem;">📄 {report['file_name']}</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                {report['row_count']:,} rows × {report['col_count']} columns
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Row 2: Data Availability + Key Insights
    b_left, b_right = st.columns([1, 1], gap="large")
    
    with b_left:
        st.subheader("📅 Data Availability")
        st.caption("Data freshness and time distribution")
        
        # Data freshness
        freshness = report.get("data_freshness", {})
        if freshness.get("max_date"):
            lag = freshness['days_lag']
            status = freshness['status']
            
            if status == 'Fresh':
                lag_color = "#00c853"
            elif status == 'Recent':
                lag_color = "#f9a825"
            elif status == 'Stale':
                lag_color = "#fb8c00"
            else:
                lag_color = "#e53935"
            
            st.markdown(f"""
            <div style="background:#f8f9fa; border-left:3px solid {lag_color};
                        padding:8px 12px; border-radius:4px; margin-bottom:12px;">
                <span style="font-weight:600; font-size:0.9rem;">{status}</span><br>
                <span style="font-size:0.82rem; color:#555;">
                    Latest data: {freshness['max_date']} ({lag} days ago)
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # Time distribution
        time_dist = report.get("time_distribution", {})
        if time_dist.get("distribution"):
            # Show growth trend if available
            if time_dist.get("growth_trend") is not None:
                growth = time_dist["growth_trend"]
                if growth > 0:
                    growth_color, growth_icon = "#00c853", "📈"
                elif growth < 0:
                    growth_color, growth_icon = "#e53935", "📉"
                else:
                    growth_color, growth_icon = "#f9a825", "➡️"
                
                st.markdown(f"""
                <div style="background:#f8f9fa; border-left:3px solid {growth_color};
                            padding:8px 12px; border-radius:4px; margin-bottom:12px;">
                    <span style="font-weight:600; font-size:0.9rem;">{growth_icon} Quarter-over-Quarter Growth</span><br>
                    <span style="font-size:0.82rem; color:#555;">
                        {growth:+.1f}% vs previous quarter
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            dist_df = pd.DataFrame([
                {"Period": period, "Count": count}
                for period, count in time_dist["distribution"].items()
            ])
            st.dataframe(dist_df, width='stretch', hide_index=True)
            st.bar_chart(dist_df.set_index("Period")["Count"], height=200)
            st.caption(f"Based on column: `{time_dist['date_column']}`")
        elif time_dist.get("message"):
            st.info(f"ℹ️ {time_dist['message']}")
        else:
            st.info("ℹ️ No time distribution data available")
    
    with b_right:
        st.subheader("🧠 Key Insights")
        st.caption("Automated findings from the EDA engine")
        
        # Sampling info (for database mode)
        if st.session_state.mode == 'database':
            sampling_info = report.get("sampling_info", "")
            if sampling_info:
                st.info(f"ℹ️ {sampling_info}")
        
        # Overall completeness score
        completeness = report.get("completeness", {})
        if completeness.get("overall_score") is not None:
            overall_score = completeness["overall_score"]
            if overall_score >= 95:
                comp_color, comp_status = "#00c853", "🟢 Excellent"
            elif overall_score >= 85:
                comp_color, comp_status = "#f9a825", "🟡 Good"
            elif overall_score >= 70:
                comp_color, comp_status = "#fb8c00", "🟠 Fair"
            else:
                comp_color, comp_status = "#e53935", "🔴 Poor"
            
            st.markdown(f"""
            <div style="background:#f8f9fa; border-left:3px solid {comp_color};
                        padding:8px 12px; border-radius:4px; margin-bottom:12px;">
                <span style="font-weight:600; font-size:0.9rem;">{comp_status}</span><br>
                <span style="font-size:0.82rem; color:#555;">
                    Overall Data Completeness: {overall_score:.1f}%
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # Volume insight
        row_count = report['row_count']
        if row_count > 1_000_000:
            st.markdown(f"""
            <div style="background:#f8f9fa; border-left:3px solid #667eea;
                        padding:8px 12px; border-radius:4px; margin-bottom:8px;">
                <span style="font-weight:600; font-size:0.9rem;">📊 Large Dataset</span><br>
                <span style="font-size:0.82rem; color:#555;">
                    {row_count:,} rows - consider sampling for analysis
                </span>
            </div>
            """, unsafe_allow_html=True)
        elif row_count < 1000:
            st.markdown(f"""
            <div style="background:#f8f9fa; border-left:3px solid #f9a825;
                        padding:8px 12px; border-radius:4px; margin-bottom:8px;">
                <span style="font-weight:600; font-size:0.9rem;">📊 Small Dataset</span><br>
                <span style="font-size:0.82rem; color:#555;">
                    {row_count:,} rows - limited statistical significance
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#f8f9fa; border-left:3px solid #00c853;
                        padding:8px 12px; border-radius:4px; margin-bottom:8px;">
                <span style="font-weight:600; font-size:0.9rem;">📊 Medium Dataset</span><br>
                <span style="font-size:0.82rem; color:#555;">
                    {row_count:,} rows - good for analysis
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    # Row 3: Column Classification
    st.divider()
    st.subheader("📋 Column Classification")
    st.caption("Columns grouped by data type")
    
    classification = report.get("classification", {})
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        for cat in ['ID/Key Columns', 'Numeric Columns']:
            cols = classification.get(cat, [])
            if cols:
                st.markdown(f"**{cat}** ({len(cols)})")
                st.write(", ".join(cols[:10]))
                if len(cols) > 10:
                    st.caption(f"... and {len(cols) - 10} more")
    
    with col_right:
        for cat in ['Date/Time Columns', 'Text/Other Columns']:
            cols = classification.get(cat, [])
            if cols:
                st.markdown(f"**{cat}** ({len(cols)})")
                st.write(", ".join(cols[:10]))
                if len(cols) > 10:
                    st.caption(f"... and {len(cols) - 10} more")
    
    # Row 3.5: Null Analysis
    st.divider()
    st.subheader("🔍 Null Analysis")
    st.caption("ID/Key columns with highest null percentages")
    
    null_percentages = report.get("null_percentages", [])
    if null_percentages:
        has_nulls = False
        for col, null_pct, null_count in null_percentages:
            if null_pct > 0:
                has_nulls = True
                icon = "🔴" if null_pct > 20 else "🟡" if null_pct > 5 else "🟢"
                st.markdown(
                    f"<p style='margin-bottom:2px; font-size:0.88rem;'>"
                    f"{icon} <b>{col}</b> — {null_pct:.1f}% null ({null_count:,} rows)</p>",
                    unsafe_allow_html=True,
                )
                st.progress(min(null_pct / 100, 1.0))
        if not has_nulls:
            st.success("✅ No null values found in ID/Key columns")
    else:
        st.info("No ID/Key columns found for null analysis.")
    
    # Row 3.6: Top Values Analysis
    st.divider()
    st.subheader("📊 Top Values Analysis")
    st.caption("Most frequent values in categorical columns (5-15 distinct values)")
    
    top_values = report.get("top_values", {})
    if top_values:
        # Use two-column layout
        t_left, t_right = st.columns([1, 1], gap="large")
        
        col_items = list(top_values.items())
        
        with t_left:
            for col, values in col_items[:len(col_items)//2 + len(col_items)%2]:
                st.markdown(f"**{col}**")
                for val in values:
                    st.markdown(f"- `{val['value']}`: {val['count']:,} ({val['percentage']}%)")
                st.divider()
        
        with t_right:
            for col, values in col_items[len(col_items)//2 + len(col_items)%2:]:
                st.markdown(f"**{col}**")
                for val in values:
                    st.markdown(f"- `{val['value']}`: {val['count']:,} ({val['percentage']}%)")
                st.divider()
    else:
        st.info("ℹ️ No categorical columns with 5-15 distinct values found")
    
    # Row 3.7: Column Cardinality
    st.divider()
    st.subheader("🎯 Column Cardinality")
    st.caption("Unique value ratio analysis - identifies high/low cardinality columns")
    
    cardinality = report.get("column_cardinality", {})
    if cardinality:
        card_df = pd.DataFrame([
            {
                "Column": col,
                "Unique Count": details['unique_count'],
                "Cardinality Ratio": details['cardinality_ratio'],
                "Type": details['type']
            }
            for col, details in cardinality.items()
        ]).sort_values("Cardinality Ratio", ascending=False)
        st.dataframe(card_df.head(15), width='stretch', hide_index=True)
    else:
        st.info("ℹ️ Column cardinality analysis not available")
    
    # Row 4: Schema Preview
    st.divider()
    st.subheader("📑 Schema Preview")
    st.caption("Column structure and data types")
    
    schema_df = report.get("schema_df")
    if schema_df is not None:
        st.dataframe(schema_df, width='stretch', hide_index=True)
    
    # Row 5: Data Preview (only for file mode)
    if st.session_state.mode == 'file' and st.session_state.df is not None:
        st.divider()
        st.subheader("👁️ Data Preview")
        st.caption("First 10 rows of the dataset")
        
        st.dataframe(st.session_state.df.head(10), width='stretch', hide_index=True)
    
    # Footer
    st.divider()
    st.caption(f"Analysis completed in {report['execution_time']:.2f} seconds")
