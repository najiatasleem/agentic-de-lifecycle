"""
EDA Engine for File Upload (Excel/CSV)
Pandas-based exploratory data analysis for uploaded files
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time


# ------------------------------------------------------------
# FILE LOADING
# ------------------------------------------------------------

def load_file(file_path, file_type=None):
    """
    Load Excel or CSV file into pandas DataFrame.
    
    Args:
        file_path: Path to the file
        file_type: 'csv', 'excel', or None (auto-detect)
    
    Returns:
        DataFrame with loaded data
    """
    if file_type is None:
        if file_path.endswith('.csv'):
            file_type = 'csv'
        elif file_path.endswith(('.xlsx', '.xls')):
            file_type = 'excel'
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel.")
    
    if file_type == 'csv':
        df = pd.read_csv(file_path)
    elif file_type == 'excel':
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    return df


# ------------------------------------------------------------
# SCHEMA INFERENCE
# ------------------------------------------------------------

def infer_schema(df):
    """
    Infer schema from DataFrame.
    
    Returns:
        schema_df: DataFrame with column info (Column Name, Data Type, Non-Null Count)
        row_count: Total number of rows
    """
    schema_data = []
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null_count = df[col].notna().sum()
        schema_data.append({
            'Column Name': col,
            'Data Type': dtype,
            'Non-Null Count': non_null_count
        })
    
    schema_df = pd.DataFrame(schema_data)
    row_count = len(df)
    
    return schema_df, row_count


# ------------------------------------------------------------
# PRIMARY KEY DETECTION
# ------------------------------------------------------------

def detect_primary_key(df, schema_df):
    """
    Detect primary key from column naming patterns.
    Returns the column name that is most likely to be a primary key.
    """
    # Priority patterns for PK detection
    pk_patterns = [
        ['_id', 'id'],  # Highest priority
        ['_pk', 'pk'],
        ['uuid', 'key'],
        ['code'],
    ]
    
    for patterns in pk_patterns:
        for col in df.columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in patterns):
                # Check if it's reasonably unique (cardinality > 0.9)
                cardinality = df[col].nunique() / len(df) if len(df) > 0 else 0
                if cardinality > 0.9:
                    return col
    
    return None


def is_good_primary_key(df, col):
    """
    Check if a column is a good primary key candidate.
    Returns True if column is unique and not categorical.
    """
    if col not in df.columns:
        return False
    
    # Check uniqueness
    cardinality = df[col].nunique() / len(df) if len(df) > 0 else 0
    if cardinality < 0.9:
        return False
    
    # Check if it's not categorical (too many distinct values for a categorical column)
    # If it has very high cardinality, it's likely an ID
    return True


# ------------------------------------------------------------
# COLUMN CLASSIFICATION
# ------------------------------------------------------------

def classify_columns(schema_df):
    """
    Classify columns by data type.
    
    Returns:
        dict with categories: ID/Key, Numeric, Date/Time, Text/Other
    """
    classification = {
        'ID/Key Columns': [],
        'Numeric Columns': [],
        'Date/Time Columns': [],
        'Text/Other Columns': []
    }
    
    for _, row in schema_df.iterrows():
        col = row['Column Name']
        dtype = row['Data Type'].lower()
        
        # ID/Key patterns
        if any(kw in col.lower() for kw in ['_id', 'id', '_key', '_pk', 'uuid']):
            classification['ID/Key Columns'].append(col)
        # Numeric types
        elif any(dt in dtype for dt in ['int', 'float', 'decimal']):
            classification['Numeric Columns'].append(col)
        # Date/Time types
        elif any(dt in dtype for dt in ['datetime', 'timestamp', 'date']):
            classification['Date/Time Columns'].append(col)
        # Text/Other
        else:
            classification['Text/Other Columns'].append(col)
    
    return classification


# ------------------------------------------------------------
# NULL ANALYSIS
# ------------------------------------------------------------

def run_null_analysis(df, classification, row_count, sample_cols=5):
    """
    Run null analysis on ID/Key columns.
    
    Returns:
        list of (col, null_pct, null_count) sorted by null_pct descending
    """
    key_columns = classification.get('ID/Key Columns', [])[:sample_cols]
    
    if not key_columns:
        return []
    
    null_results = []
    for col in key_columns:
        if col in df.columns:
            null_count = df[col].isna().sum()
            null_pct = (null_count / row_count) * 100 if row_count > 0 else 0
            null_results.append((col, null_pct, null_count))
    
    return sorted(null_results, key=lambda x: x[1], reverse=True)


# ------------------------------------------------------------
# DUPLICATE DETECTION
# ------------------------------------------------------------

def run_duplicate_check(df, primary_key=None, sample_size=500_000):
    """
    Check for duplicate rows based on primary key or all columns.
    
    Returns:
        dict with duplicate count, percentage, and sample duplicates
    """
    if primary_key and primary_key in df.columns:
        # Check duplicates on primary key
        dup_count = df[primary_key].duplicated().sum()
    else:
        # Check duplicates on all columns
        dup_count = df.duplicated().sum()
    
    row_count = len(df)
    dup_pct = (dup_count / row_count) * 100 if row_count > 0 else 0
    
    # Get sample duplicates
    if primary_key and primary_key in df.columns:
        sample_dupes = df[df[primary_key].duplicated(keep=False)].head(10)
    else:
        sample_dupes = df[df.duplicated(keep=False)].head(10)
    
    return {
        'dup_count': dup_count,
        'dup_pct': dup_pct,
        'sample_dupes': sample_dupes.to_dict('records') if not sample_dupes.empty else []
    }


# ------------------------------------------------------------
# DATA FRESHNESS ANALYSIS
# ------------------------------------------------------------

def analyze_data_freshness(df, schema_df):
    """
    Analyze data freshness from date columns.
    
    Returns:
        dict with max_date, days_lag, and status
    """
    date_cols = []
    
    for _, row in schema_df.iterrows():
        col = row['Column Name']
        dtype = row['Data Type'].lower()
        if any(dt in dtype for dt in ['datetime', 'timestamp', 'date']):
            date_cols.append(col)
    
    if not date_cols:
        return {
            'max_date': None,
            'days_lag': None,
            'status': 'No date columns'
        }
    
    # Try to find the most recent date across all date columns
    max_date = None
    for col in date_cols:
        if col in df.columns:
            try:
                col_max = pd.to_datetime(df[col], errors='coerce').max()
                if pd.notna(col_max):
                    if max_date is None or col_max > max_date:
                        max_date = col_max
            except:
                continue
    
    if max_date is None:
        return {
            'max_date': None,
            'days_lag': None,
            'status': 'No valid dates'
        }
    
    # Calculate days lag
    today = pd.Timestamp.now()
    days_lag = (today - max_date).days
    
    # Determine status
    if days_lag <= 1:
        status = 'Fresh'
    elif days_lag <= 7:
        status = 'Recent'
    elif days_lag <= 30:
        status = 'Stale'
    else:
        status = 'Very Stale'
    
    return {
        'max_date': max_date.strftime('%Y-%m-%d'),
        'days_lag': days_lag,
        'status': status
    }


# ------------------------------------------------------------
# TIME DISTRIBUTION ANALYSIS
# ------------------------------------------------------------

def analyze_time_distribution(df, schema_df):
    """
    Analyze time distribution (quarterly) from date columns.
    
    Returns:
        dict with distribution, date_column, and growth_trend
    """
    date_cols = []
    
    for _, row in schema_df.iterrows():
        col = row['Column Name']
        dtype = row['Data Type'].lower()
        if any(dt in dtype for dt in ['datetime', 'timestamp', 'date']):
            date_cols.append(col)
    
    if not date_cols:
        return {
            'distribution': {},
            'date_column': None,
            'growth_trend': None,
            'message': 'No date columns found'
        }
    
    # Use first date column
    date_col = date_cols[0]
    
    try:
        # Convert to datetime
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Filter out null dates
        valid_dates = df[df[date_col].notna()]
        
        if valid_dates.empty:
            return {
                'distribution': {},
                'date_column': date_col,
                'growth_trend': None,
                'message': 'No valid dates in column'
            }
        
        # Fiscal quarter logic: Feb-Apr=Q1, May-Jul=Q2, Aug-Oct=Q3, Nov-Jan=Q4
        def get_fiscal_quarter(dt):
            month = dt.month
            if 2 <= month <= 4:
                quarter = 'Q1'
                fiscal_year = dt.year
            elif 5 <= month <= 7:
                quarter = 'Q2'
                fiscal_year = dt.year
            elif 8 <= month <= 10:
                quarter = 'Q3'
                fiscal_year = dt.year
            else:  # Nov, Dec, Jan
                quarter = 'Q4'
                fiscal_year = dt.year if month != 1 else dt.year - 1
            return f"{quarter} {fiscal_year}"
        
        valid_dates['quarter'] = valid_dates[date_col].apply(get_fiscal_quarter)
        quarterly_counts = valid_dates['quarter'].value_counts().sort_index(ascending=False).head(20)
        
        distribution = {f"{period}": count for period, count in quarterly_counts.items()}
        
        # Calculate growth trend (current vs previous quarter)
        growth_trend = None
        if len(quarterly_counts) >= 2:
            current_count = quarterly_counts.iloc[0]
            prev_count = quarterly_counts.iloc[1]
            if prev_count > 0:
                growth_pct = ((current_count - prev_count) / prev_count) * 100
                growth_trend = round(growth_pct, 1)
        
        return {
            'distribution': distribution,
            'date_column': date_col,
            'growth_trend': growth_trend,
            'message': None
        }
    except Exception as e:
        return {
            'distribution': {},
            'date_column': date_col,
            'growth_trend': None,
            'message': f'Error: {str(e)}'
        }


# ------------------------------------------------------------
# TOP VALUES ANALYSIS
# ------------------------------------------------------------

def analyze_top_values(df, schema_df, top_n=5, max_cols=20):
    """
    Analyze top N values for categorical columns with 5-15 distinct values.
    
    Returns:
        dict: {column_name: [{value, count, percentage}]}
    """
    top_values = {}
    
    # Limit to first max_cols columns
    for _, row in schema_df.head(max_cols).iterrows():
        col = row['Column Name']
        dtype = row['Data Type'].lower()
        
        # Focus on text/object columns that are likely categorical
        if 'object' in dtype or 'str' in dtype:
            if not any(kw in col.lower() for kw in ['id', 'email', 'phone', 'url', 'description', 'notes', 'address']):
                try:
                    # Check cardinality
                    distinct_count = df[col].nunique()
                    
                    # Only analyze columns with 5-15 distinct values
                    if 5 <= distinct_count <= 15:
                        value_counts = df[col].value_counts().head(top_n)
                        total = df[col].notna().sum()
                        
                        top_values[col] = [
                            {
                                'value': str(val),
                                'count': int(count),
                                'percentage': round((count / total) * 100, 1) if total > 0 else 0
                            }
                            for val, count in value_counts.items()
                        ]
                except:
                    continue
    
    return top_values


# ------------------------------------------------------------
# COLUMN CARDINALITY ANALYSIS
# ------------------------------------------------------------

def analyze_column_cardinality(df, schema_df, row_count, max_cols=30):
    """
    Analyze column cardinality (unique values ratio).
    
    Returns:
        dict: {column_name: {unique_count, cardinality_ratio, type}}
    """
    cardinality = {}
    
    # Limit to first max_cols columns
    for _, row in schema_df.head(max_cols).iterrows():
        col = row['Column Name']
        
        try:
            unique_count = df[col].nunique()
            
            if row_count > 0:
                card_ratio = unique_count / row_count
            else:
                card_ratio = 0
            
            # Classify cardinality type
            if card_ratio > 0.9:
                card_type = "High (near-unique)"
            elif card_ratio > 0.5:
                card_type = "Medium-High"
            elif card_ratio > 0.1:
                card_type = "Medium"
            elif card_ratio > 0.01:
                card_type = "Low"
            else:
                card_type = "Very Low (few distinct values)"
            
            cardinality[col] = {
                'unique_count': int(unique_count),
                'cardinality_ratio': round(card_ratio, 4),
                'type': card_type
            }
        except:
            continue
    
    return cardinality


# ------------------------------------------------------------
# DATA COMPLETENESS SCORE
# ------------------------------------------------------------

def calculate_completeness_score(df, schema_df, row_count, max_cols=30):
    """
    Calculate overall data completeness score across columns.
    
    Returns:
        dict: {overall_score, column_scores}
    """
    column_scores = {}
    total_nulls = 0
    
    # Limit to first max_cols columns
    limited_schema = schema_df.head(max_cols)
    total_cells = len(limited_schema) * row_count if row_count > 0 else 0
    
    for _, row in limited_schema.iterrows():
        col = row['Column Name']
        
        if col in df.columns:
            null_count = df[col].isna().sum()
            
            if row_count > 0:
                null_pct = (null_count / row_count) * 100
                completeness = 100 - null_pct
            else:
                null_pct = 0
                completeness = 100
            
            column_scores[col] = {
                'null_count': int(null_count),
                'null_percentage': round(null_pct, 2),
                'completeness': round(completeness, 2)
            }
            total_nulls += null_count
    
    # Calculate overall score
    if total_cells > 0:
        overall_score = 100 - ((total_nulls / total_cells) * 100)
    else:
        overall_score = 100
    
    return {
        'overall_score': round(overall_score, 2),
        'column_scores': column_scores
    }


# ------------------------------------------------------------
# FULL EDA ORCHESTRATOR
# ------------------------------------------------------------

def run_full_eda_file(df, file_name, primary_key=None):
    """
    Run complete EDA pipeline on uploaded file.
    
    Args:
        df: pandas DataFrame with loaded data
        file_name: Name of the uploaded file
        primary_key: Optional primary key column name
    
    Returns:
        report dict containing all EDA results
    """
    start_time = time.time()
    
    try:
        schema_df, row_count = infer_schema(df)
        classification = classify_columns(schema_df)
        null_percentages = run_null_analysis(df, classification, row_count)
        
        # Smart primary key detection if not provided
        if primary_key is None:
            # Try first column
            if len(df.columns) > 0:
                first_col = df.columns[0]
                if is_good_primary_key(df, first_col):
                    primary_key = first_col
                else:
                    # Fall back to naming pattern detection
                    primary_key = detect_primary_key(df, schema_df)
                    if primary_key is None:
                        # Last resort: use first column anyway
                        primary_key = first_col
        
        dup_results = run_duplicate_check(df, primary_key)
        data_freshness = analyze_data_freshness(df, schema_df)
        time_distribution = analyze_time_distribution(df, schema_df)
        top_values = analyze_top_values(df, schema_df)
        column_cardinality = analyze_column_cardinality(df, schema_df, row_count)
        completeness = calculate_completeness_score(df, schema_df, row_count)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise Exception(f"EDA failed: {str(e)}\n\n{error_details}")
    
    return {
        'file_name': file_name,
        'row_count': row_count,
        'col_count': len(df.columns),
        'schema_df': schema_df,
        'primary_key': primary_key,
        'classification': classification,
        'null_percentages': null_percentages,
        'dup_results': dup_results,
        'data_freshness': data_freshness,
        'time_distribution': time_distribution,
        'top_values': top_values,
        'column_cardinality': column_cardinality,
        'completeness': completeness,
        'execution_time': time.time() - start_time,
        'sampling_info': f"Analyzed {min(30, len(schema_df))} of {len(schema_df)} columns (prioritized by importance)"
    }
