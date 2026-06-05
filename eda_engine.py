import psycopg2
import pandas as pd
import time
from collections import defaultdict

# ============================================================
# EDA ENGINE - Reusable Agentic EDA Module
# Version: 1.0
# ============================================================

CLASSIFICATION_PATTERNS = {
    'Date Columns':    ['_dts', '_dt', '_date', 'date', 'time'],
    'ID/Key Columns':  ['_id', 'id', '_key', '_nbr', '_pk'],
    'Code Columns':    ['_cd', '_code', 'code', '_type'],
    'Text Columns':    ['_txt', '_desc', '_nm', 'name', '_addr'],
    'Flag Columns':    ['_flg', '_flag', 'flag', '_ind', 'indicator'],
}


# ------------------------------------------------------------
# CONNECTION
# ------------------------------------------------------------

def connect(db_config):
    """Connect to PostgreSQL and return (conn, cursor)."""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    return conn, cursor


# ------------------------------------------------------------
# SCHEMA
# ------------------------------------------------------------

def get_schema(cursor, table_name):
    """
    Fetch schema and row count for a table.
    Returns (schema_df, row_count, primary_key).
    primary_key is detected from actual PK constraints or DISTRIBUTED BY clause.
    """
    schema_query = """
        SELECT column_name, data_type, ordinal_position
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """
    cursor.execute(schema_query, (table_name,))
    rows = cursor.fetchall()
    schema_df = pd.DataFrame(rows, columns=['Column Name', 'Data Type', 'Position'])

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]

    # Try to get actual primary key from constraints
    pk_query = """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_name = %s
    """
    cursor.execute(pk_query, (table_name,))
    pk_result = cursor.fetchone()
    
    if pk_result:
        primary_key = pk_result[0]
    else:
        # Fallback: try to get DISTRIBUTED BY column (Greenplum/PostgreSQL)
        # This requires querying pg_class for Greenplum distribution keys
        try:
            dist_query = """
                SELECT attname
                FROM pg_attribute
                JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
                JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid
                WHERE pg_class.relname = %s
                    AND attnum IN (
                        SELECT unnest(attrnums)
                        FROM gp_distribution_policy
                        WHERE localoid = pg_class.oid
                    )
                LIMIT 1
            """
            cursor.execute(dist_query, (table_name,))
            dist_result = cursor.fetchone()
            if dist_result:
                primary_key = dist_result[0]
            else:
                # Final fallback: first column
                primary_key = schema_df.iloc[0]['Column Name'] if len(schema_df) > 0 else None
        except Exception:
            # If gp_distribution_policy doesn't exist (not Greenplum), fallback to first column
            primary_key = schema_df.iloc[0]['Column Name'] if len(schema_df) > 0 else None

    return schema_df, row_count, primary_key


# ------------------------------------------------------------
# CLASSIFICATION
# ------------------------------------------------------------

def classify_columns(schema_df):
    """
    Classify every column by naming patterns.
    Returns dict: {category: [col_names]}.
    """
    results = defaultdict(list)

    for _, row in schema_df.iterrows():
        col_name = row['Column Name']
        col_lower = col_name.lower()
        data_type = row['Data Type']
        classified = False

        for category, keywords in CLASSIFICATION_PATTERNS.items():
            if any(kw in col_lower for kw in keywords):
                results[category].append(col_name)
                classified = True
                break

        if not classified:
            if 'numeric' in data_type or 'int' in data_type:
                results['Numeric Columns'].append(col_name)
            else:
                results['Other Columns'].append(col_name)

    return dict(results)


# ------------------------------------------------------------
# TABLE JOIN DETECTION
# ------------------------------------------------------------

def detect_table_joins(cursor, table_name):
    """
    Detect foreign key relationships and potential join opportunities.
    Returns dict: {related_table: {join_column, fk_constraint}}.
    """
    joins = {}

    # Get foreign key constraints
    fk_query = """
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s
    """
    cursor.execute(fk_query, (table_name,))
    fk_rows = cursor.fetchall()

    for col, foreign_table, foreign_col, constraint_name in fk_rows:
        joins[foreign_table] = {
            'join_column': col,
            'foreign_column': foreign_col,
            'constraint_name': constraint_name,
            'type': 'foreign_key'
        }

    # Detect potential joins by naming pattern (columns ending in _id)
    pattern_query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
            AND (column_name LIKE '%%_id' OR column_name LIKE '%%_fk')
    """
    cursor.execute(pattern_query, (table_name,))
    pattern_rows = cursor.fetchall()

    for (col,) in pattern_rows:
        # Try to guess the table name from the column
        potential_table = col.replace('_id', '').replace('_fk', '')
        # Check if this table exists
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = %s
            LIMIT 1
        """, (potential_table,))
        result = cursor.fetchone()
        if result and result[0] not in joins:
            joins[result[0]] = {
                'join_column': col,
                'foreign_column': 'id',
                'constraint_name': None,
                'type': 'potential'
            }

    return joins


# ------------------------------------------------------------
# DATA FRESHNESS ANALYSIS
# ------------------------------------------------------------

def analyze_data_freshness(cursor, table_name, schema_df):
    """
    Analyze data freshness - most recent date and data lag.
    Returns dict: {max_date, days_lag, date_column_used}.
    """
    # Find date columns (same logic as time distribution)
    date_columns = []
    for _, row in schema_df.iterrows():
        col = row['Column Name']
        col_lower = col.lower()
        data_type = row['Data Type'].lower()
        if 'date' in data_type or 'timestamp' in data_type:
            if any(kw in col_lower for kw in ['_dts', '_dt', '_date', 'date', 'time', 'crt_dts', 'created_dts', 'src_crt', 'crt_dt', 'created_dt']):
                date_columns.append(col)
    
    if not date_columns:
        return {'max_date': None, 'days_lag': None, 'date_column': None, 'message': 'No date columns found'}
    
    # Use the first date column found
    date_col = date_columns[0]
    
    try:
        max_date_query = f"""
            SELECT MAX("{date_col}") as max_date
            FROM {table_name}
            WHERE "{date_col}" IS NOT NULL
        """
        cursor.execute(max_date_query)
        result = cursor.fetchone()
        
        if result and result[0]:
            max_date = result[0]
            # Calculate days lag from today
            from datetime import datetime
            today = datetime.now().date()
            if isinstance(max_date, datetime):
                max_date = max_date.date()
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
                'max_date': str(max_date),
                'days_lag': days_lag,
                'date_column': date_col,
                'status': status,
                'message': None
            }
        else:
            return {'max_date': None, 'days_lag': None, 'date_column': date_col, 'message': 'No valid dates found'}
    except Exception as e:
        return {'max_date': None, 'days_lag': None, 'date_column': date_col, 'message': f'Error: {str(e)}'}


# ------------------------------------------------------------
# TIME-BASED DISTRIBUTION ANALYSIS
# ------------------------------------------------------------

def analyze_time_distribution(cursor, table_name, schema_df, sample_size=1_000_000):
    """
    Analyze data distribution over time (quarterly/yearly).
    Returns dict: {period: count, date_column_used}.
    Selects the most prominent business date column based on table context.
    """
    # Find all date columns - strict check on data type first
    date_columns = []
    for _, row in schema_df.iterrows():
        col = row['Column Name']
        col_lower = col.lower()
        data_type = row['Data Type'].lower()
        # Strict check: must be a date/timestamp data type
        if 'date' in data_type or 'timestamp' in data_type:
            # Then apply name pattern matching as secondary filter
            if any(kw in col_lower for kw in ['_dts', '_dt', '_date', 'date', 'time', 'crt_dts', 'created_dts', 'src_crt', 'crt_dt', 'created_dt']):
                date_columns.append(col)
    
    if not date_columns:
        return {'distribution': {}, 'date_column': None, 'message': 'No date columns found'}
    
    # Smart selection: prioritize business-relevant date columns based on table name
    table_lower = table_name.lower()
    date_col = None
    
    # Priority patterns based on table context
    priority_patterns = [
        # Order-related tables
        (['order', 'sales', 'purchase'], ['order_date', 'order_dts', 'sales_date', 'purchase_date']),
        # Work order tables (expanded patterns for sfdc_wo_dtl)
        (['wo', 'work_order', 'workorder'], ['wo_date', 'work_order_date', 'created_dts', 'created_date', 'src_crt_dts', 'crt_dts', 'src_crt']),
        # Case/ticket tables
        (['case', 'ticket', 'incident'], ['case_created_date', 'created_date', 'created_dts', 'case_date', 'src_crt_dts', 'crt_dts']),
        # Transaction tables
        (['transaction', 'txn', 'trans'], ['transaction_date', 'txn_date', 'trans_date', 'src_crt_dts', 'crt_dts']),
        # Customer tables
        (['customer', 'cust', 'client'], ['created_date', 'created_dts', 'signup_date', 'registration_date', 'src_crt_dts', 'crt_dts']),
        # General fallback patterns (expanded)
        (None, ['created_date', 'created_dts', 'modified_date', 'updated_date', 'last_updated', 'src_crt_dts', 'crt_dts', 'src_crt']),
    ]
    
    # Try to find best match based on table context
    for table_keywords, date_keywords in priority_patterns:
        if table_keywords is None or any(kw in table_lower for kw in table_keywords):
            for date_col_candidate in date_columns:
                if any(kw in date_col_candidate.lower() for kw in date_keywords):
                    date_col = date_col_candidate
                    break
            if date_col:
                break
    
    # Fallback: use first date column if no smart match
    if not date_col:
        date_col = date_columns[0]
    
    try:
        # Fiscal quarter logic: Feb-Apr=Q1, May-Jul=Q2, Aug-Oct=Q3, Nov-Jan=Q4
        fiscal_quarter_query = f"""
            SELECT 
                CASE 
                    WHEN EXTRACT(MONTH FROM "{date_col}") BETWEEN 2 AND 4 THEN 'Q1'
                    WHEN EXTRACT(MONTH FROM "{date_col}") BETWEEN 5 AND 7 THEN 'Q2'
                    WHEN EXTRACT(MONTH FROM "{date_col}") BETWEEN 8 AND 10 THEN 'Q3'
                    ELSE 'Q4'
                END as quarter,
                CASE 
                    WHEN EXTRACT(MONTH FROM "{date_col}") = 1 THEN EXTRACT(YEAR FROM "{date_col}") - 1
                    ELSE EXTRACT(YEAR FROM "{date_col}")
                END as fiscal_year,
                COUNT(*) as count
            FROM {table_name}
            WHERE "{date_col}" IS NOT NULL
            GROUP BY quarter, fiscal_year
            ORDER BY fiscal_year DESC, quarter DESC
            LIMIT 20
        """
        cursor.execute(fiscal_quarter_query)
        quarterly_results = cursor.fetchall()
        
        # Format as "Q1 2024"
        distribution = {f"Q{row[0]} {int(row[1])}": row[2] for row in quarterly_results}
        
        # Calculate growth trend (current vs previous quarter)
        growth_trend = None
        if len(quarterly_results) >= 2:
            current_count = quarterly_results[0][2]
            prev_count = quarterly_results[1][2]
            if prev_count > 0:
                growth_pct = ((current_count - prev_count) / prev_count) * 100
                growth_trend = round(growth_pct, 1)
        
        return {
            'distribution': distribution,
            'date_column': date_col,
            'period_type': 'fiscal_quarterly',
            'growth_trend': growth_trend,
            'message': None
        }
    except Exception as e:
        # Try without truncation as fallback
        try:
            fallback_query = f"""
                SELECT 
                    DATE("{date_col}") as period,
                    COUNT(*) as count
                FROM {table_name}
                WHERE "{date_col}" IS NOT NULL
                GROUP BY DATE("{date_col}")
                ORDER BY period DESC
                LIMIT 20
            """
            cursor.execute(fallback_query)
            fallback_results = cursor.fetchall()
            
            distribution = {str(row[0]): row[1] for row in fallback_results}
            
            return {
                'distribution': distribution,
                'date_column': date_col,
                'period_type': 'daily',
                'message': None
            }
        except Exception as e2:
            return {'distribution': {}, 'date_column': date_col, 'message': f'Error: {str(e2)}'}


# ------------------------------------------------------------
# COLUMN PRIORITIZATION
# ------------------------------------------------------------

def prioritize_columns(schema_df, primary_key, fk_columns=None, indexed_columns=None):
    """
    Prioritize columns by importance for sampling.
    Returns ordered list of column names.
    """
    if fk_columns is None:
        fk_columns = set()
    if indexed_columns is None:
        indexed_columns = set()
    
    priorities = []
    
    for _, row in schema_df.iterrows():
        col = row['Column Name']
        priority = 0
        
        # Priority 5: Primary key (highest)
        if col == primary_key:
            priority = 5
        # Priority 4: Foreign keys
        elif col in fk_columns:
            priority = 4
        # Priority 3: Indexed columns
        elif col in indexed_columns:
            priority = 3
        # Priority 2: ID/Key columns
        elif any(kw in col.lower() for kw in ['_id', 'id', '_key', '_pk']):
            priority = 2
        # Priority 1: Date columns
        elif any(kw in col.lower() for kw in ['_dts', '_dt', '_date', 'date']):
            priority = 1
        # Priority 0: Other columns
        else:
            priority = 0
        
        priorities.append((col, priority))
    
    # Sort by priority (descending), then by original order
    priorities.sort(key=lambda x: (-x[1], schema_df[schema_df['Column Name'] == x[0]].index[0]))
    
    return [col for col, _ in priorities]


# ------------------------------------------------------------
# TOP N ANALYSIS FOR CATEGORICAL COLUMNS
# ------------------------------------------------------------

def analyze_top_values(cursor, table_name, schema_df, top_n=5, max_cols=20):
    """
    Analyze top N values for categorical columns with 5-15 distinct values.
    Limited to top columns to avoid performance issues.
    Returns dict: {column_name: [{value, count, percentage}]}.
    """
    top_values = {}
    
    # Limit to first max_cols columns to avoid expensive queries on wide tables
    for _, row in schema_df.head(max_cols).iterrows():
        col = row['Column Name']
        data_type = row['Data Type'].lower()
        
        # Focus on text/varchar columns that are likely categorical
        if any(dt in data_type for dt in ['text', 'varchar', 'char']) and not any(
            kw in col.lower() for kw in ['id', 'email', 'phone', 'url', 'description', 'notes', 'address']
        ):
            try:
                # First check cardinality - only analyze columns with 5-15 distinct values
                distinct_query = f'SELECT COUNT(DISTINCT "{col}") FROM {table_name}'
                cursor.execute(distinct_query)
                distinct_count = cursor.fetchone()[0]
                
                # Only analyze columns with 5-15 distinct values (good categorical columns)
                if 5 <= distinct_count <= 15:
                    query = f"""
                        SELECT "{col}", COUNT(*) as count
                        FROM {table_name}
                        WHERE "{col}" IS NOT NULL
                        GROUP BY "{col}"
                        ORDER BY count DESC
                        LIMIT {top_n}
                    """
                    cursor.execute(query)
                    results = cursor.fetchall()
                    
                    if results:
                        # Get total count for percentage calculation
                        total_query = f'SELECT COUNT(*) FROM {table_name} WHERE "{col}" IS NOT NULL'
                        cursor.execute(total_query)
                        total = cursor.fetchone()[0]
                        
                        top_values[col] = [
                            {'value': row[0], 'count': row[1], 'percentage': round((row[1] / total) * 100, 1) if total > 0 else 0}
                            for row in results
                        ]
            except Exception:
                # Skip columns that fail to query
                continue
    
    return top_values


# ------------------------------------------------------------
# OVERALL DATA COMPLETENESS SCORE
# ------------------------------------------------------------

def calculate_completeness_score(cursor, table_name, schema_df, row_count, max_cols=30):
    """
    Calculate overall data completeness score across columns.
    Limited to top columns to avoid performance issues.
    Returns dict: {overall_score, column_scores}.
    """
    column_scores = {}
    total_nulls = 0
    
    # Limit to first max_cols columns to avoid expensive queries on wide tables
    limited_schema = schema_df.head(max_cols)
    total_cells = len(limited_schema) * row_count if row_count > 0 else 0
    
    # Build a single query to get null counts for all columns at once
    col_list = [f'COUNT(CASE WHEN "{row["Column Name"]}" IS NULL THEN 1 END) as "{row["Column Name"]}"' 
                for _, row in limited_schema.iterrows()]
    
    if col_list:
        single_query = f'SELECT {", ".join(col_list)} FROM {table_name}'
        cursor.execute(single_query)
        null_counts = cursor.fetchone()
        
        for idx, (_, row) in enumerate(limited_schema.iterrows()):
            col = row['Column Name']
            null_count = null_counts[idx]
            
            if row_count > 0:
                null_pct = (null_count / row_count) * 100
                completeness = 100 - null_pct
            else:
                null_pct = 0
                completeness = 100
            
            column_scores[col] = {
                'null_count': null_count,
                'null_percentage': round(null_pct, 2),
                'completeness': round(completeness, 2)
            }
            total_nulls += null_count
    
    # Calculate overall score (based on sampled columns)
    if total_cells > 0:
        overall_score = 100 - ((total_nulls / total_cells) * 100)
    else:
        overall_score = 100
    
    return {
        'overall_score': round(overall_score, 2),
        'column_scores': column_scores
    }


# ------------------------------------------------------------
# COLUMN CARDINALITY ANALYSIS
# ------------------------------------------------------------

def analyze_column_cardinality(cursor, table_name, schema_df, row_count, max_cols=30):
    """
    Analyze column cardinality (unique values ratio).
    Limited to top columns to avoid performance issues.
    Returns dict: {column_name: {unique_count, cardinality_ratio, type}}.
    """
    cardinality = {}
    
    # Limit to first max_cols columns to avoid expensive queries on wide tables
    for _, row in schema_df.head(max_cols).iterrows():
        col = row['Column Name']
        
        try:
            query = f'SELECT COUNT(DISTINCT "{col}") FROM {table_name}'
            cursor.execute(query)
            unique_count = cursor.fetchone()[0]
            
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
                'unique_count': unique_count,
                'cardinality_ratio': round(card_ratio, 4),
                'type': card_type
            }
        except Exception:
            # Skip columns that fail to query
            continue
    
    return cardinality


# ------------------------------------------------------------
# COLUMN USAGE ANALYSIS
# ------------------------------------------------------------

def analyze_column_usage(cursor, table_name, schema_df, primary_key):
    """
    Analyze column importance based on usage patterns.
    Returns dict: {column_name: {usage_score, reasons}}.
    """
    usage = {}

    # Get index information
    index_query = """
        SELECT
            a.attname AS column_name,
            i.relname AS index_name
        FROM pg_class t
        JOIN pg_index ix ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        WHERE t.relname = %s
    """
    cursor.execute(index_query, (table_name,))
    indexed_columns = {row[0] for row in cursor.fetchall()}

    # Get foreign key columns
    fk_query = """
        SELECT kcu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s
    """
    cursor.execute(fk_query, (table_name,))
    fk_columns = {row[0] for row in cursor.fetchall()}

    for _, row in schema_df.iterrows():
        col = row['Column Name']
        score = 0
        reasons = []

        # Primary key - highest importance
        if col == primary_key:
            score += 50
            reasons.append('Primary key')

        # Foreign key - high importance
        if col in fk_columns:
            score += 30
            reasons.append('Foreign key (used in joins)')

        # Indexed - high importance
        if col in indexed_columns:
            score += 20
            reasons.append('Has index (used for queries)')

        # ID/Key naming pattern - moderate importance
        if any(kw in col.lower() for kw in ['_id', 'id', '_key', '_pk']):
            score += 15
            reasons.append('ID/Key column pattern')

        # Date columns - often used for filtering
        if any(kw in col.lower() for kw in ['_dts', '_dt', '_date', 'date']):
            score += 10
            reasons.append('Date column (used for filtering)')

        usage[col] = {
            'usage_score': score,
            'reasons': reasons
        }

    return usage


# ------------------------------------------------------------
# NULL ANALYSIS
# ------------------------------------------------------------

def run_null_analysis(cursor, table_name, classification, row_count, sample_cols=5):
    """
    Run null analysis on top ID/Key columns using a single optimized query.
    Returns list of (col, null_pct, null_count) sorted by null_pct descending.
    """
    key_columns = classification.get('ID/Key Columns', [])[:sample_cols]

    if not key_columns:
        return []

    null_query = f"""
        SELECT {', '.join([f'COUNT({col})' for col in key_columns])}
        FROM {table_name}
    """
    cursor.execute(null_query)
    counts = cursor.fetchone()

    null_percentages = []
    for i, col in enumerate(key_columns):
        null_count = row_count - counts[i]
        null_pct = (null_count / row_count) * 100 if row_count > 0 else 0
        null_percentages.append((col, null_pct, null_count))

    null_percentages.sort(key=lambda x: x[1], reverse=True)
    return null_percentages


# ------------------------------------------------------------
# DUPLICATE / GRAIN CHECK
# ------------------------------------------------------------

def run_duplicate_check(cursor, table_name, primary_key, sample_size=500_000):
    """
    Check primary key uniqueness via sampling for performance on large tables.
    Returns dict with total, unique_keys, duplicates, dup_pct, sampled flag.
    """
    dup_query = f"""
        SELECT
            COUNT(*)                          AS total,
            COUNT(DISTINCT {primary_key})     AS unique_keys,
            COUNT(*) - COUNT(DISTINCT {primary_key}) AS duplicates
        FROM (SELECT {primary_key} FROM {table_name} LIMIT {sample_size}) sample
    """
    cursor.execute(dup_query)
    total, unique_keys, duplicates = cursor.fetchone()
    dup_pct = (duplicates / total) * 100 if total > 0 else 0

    return {
        'total':       total,
        'unique_keys': unique_keys,
        'duplicates':  duplicates,
        'dup_pct':     dup_pct,
        'sampled':     True,
        'sample_size': sample_size,
    }


# ------------------------------------------------------------
# QUALITY SCORING
# ------------------------------------------------------------

def score_quality(null_percentages, dup_results, row_count, schema_df):
    """
    Score data quality 0-100 based on nulls, duplicates, volume, complexity.
    Returns dict: {score, quality_level, risks, recommendations}.
    """
    score = 100
    risks = []
    recommendations = []

    for col, null_pct, _ in null_percentages:
        if null_pct > 20:
            score -= 15
            risks.append(f"High nulls in {col} ({null_pct:.1f}%)")
        elif null_pct > 5:
            score -= 5
            risks.append(f"Moderate nulls in {col} ({null_pct:.1f}%)")

    if dup_results['dup_pct'] > 0:
        score -= 25
        risks.append("Duplicate primary key values detected")
        recommendations.append("Fix grain violation via deduplication")

    if row_count > 100_000_000:
        score -= 5
        recommendations.append("Consider partitioning for performance")

    if len(schema_df) > 200:
        score -= 5
        recommendations.append("Consider denormalization for wide table")

    score = max(0, min(100, score))

    if score >= 85:
        quality_level = "🟢 EXCELLENT"
    elif score >= 70:
        quality_level = "🟡 GOOD"
    elif score >= 50:
        quality_level = "🟠 FAIR"
    else:
        quality_level = "🔴 POOR"

    return {
        'score':           score,
        'quality_level':   quality_level,
        'risks':           risks,
        'recommendations': recommendations,
    }


# ------------------------------------------------------------
# FULL EDA ORCHESTRATOR
# ------------------------------------------------------------

def run_full_eda(table_name, db_config, sample_size=500_000):
    """
    Run complete EDA pipeline on a table.

    Args:
        table_name  : Target table name (string)
        db_config   : Dict with host, database, user, password, port
        sample_size : Rows to sample for duplicate check (default 500K)

    Returns:
        report dict containing all EDA results
    """
    start_time = time.time()

    conn, cursor = connect(db_config)
    
    # Set autocommit to avoid transaction issues
    conn.autocommit = True

    try:
        schema_df, row_count, primary_key = get_schema(cursor, table_name)
        classification    = classify_columns(schema_df)
        null_percentages  = run_null_analysis(cursor, table_name, classification, row_count)
        dup_results       = run_duplicate_check(cursor, table_name, primary_key, sample_size)
        table_joins       = detect_table_joins(cursor, table_name)
        column_usage      = analyze_column_usage(cursor, table_name, schema_df, primary_key)
        
        # Get FK and indexed columns for prioritization
        fk_query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
        """
        cursor.execute(fk_query, (table_name,))
        fk_columns = {row[0] for row in cursor.fetchall()}
        
        index_query = f"""
            SELECT attname
            FROM pg_index
            JOIN pg_attribute ON pg_attribute.attrelid = pg_index.indrelid
                AND pg_attribute.attnum = ANY(pg_index.indkey)
            WHERE pg_index.indrelid = '{table_name}'::regclass
        """
        cursor.execute(index_query)
        indexed_columns = {row[0] for row in cursor.fetchall()}
        
        # Prioritize columns for sampling
        prioritized_cols = prioritize_columns(schema_df, primary_key, fk_columns, indexed_columns)
        prioritized_schema = schema_df[schema_df['Column Name'].isin(prioritized_cols)]
        
        data_freshness    = analyze_data_freshness(cursor, table_name, schema_df)
        time_distribution = analyze_time_distribution(cursor, table_name, schema_df)
        top_values        = analyze_top_values(cursor, table_name, prioritized_schema)
        column_cardinality = analyze_column_cardinality(cursor, table_name, prioritized_schema, row_count)
        completeness      = calculate_completeness_score(cursor, table_name, prioritized_schema, row_count)
        quality           = score_quality(null_percentages, dup_results, row_count, schema_df)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise Exception(f"EDA failed: {str(e)}\n\n{error_details}")
    finally:
        cursor.close()
        conn.close()

    return {
        'table_name':       table_name,
        'row_count':        row_count,
        'schema_df':        schema_df,
        'primary_key':      primary_key,
        'classification':   classification,
        'null_percentages': null_percentages,
        'dup_results':      dup_results,
        'table_joins':      table_joins,
        'column_usage':     column_usage,
        'data_freshness':   data_freshness,
        'time_distribution': time_distribution,
        'top_values':       top_values,
        'column_cardinality': column_cardinality,
        'completeness':     completeness,
        'quality':          quality,
        'execution_time':   time.time() - start_time,
        'sampling_info':    f"Analyzed {len(prioritized_schema)} of {len(schema_df)} columns (prioritized by importance)",
    }


# ------------------------------------------------------------
# REPORT PRINTER
# ------------------------------------------------------------

def print_report(report):
    """Print a formatted, demo-ready EDA report."""
    SEP = "=" * 60

    print(SEP)
    print("🔍 AGENTIC EDA REPORT")
    print(SEP)

    # Section 1: Schema
    print(f"\n📊 SECTION 1 — SCHEMA DETECTED")
    print(f"  Table      : {report['table_name']}")
    print(f"  Rows       : {report['row_count']:,}")
    print(f"  Columns    : {len(report['schema_df'])}")
    print(f"  Primary Key: {report['primary_key']}")
    print(f"  ℹ️  PK detected from database constraints or DISTRIBUTED BY clause")

    # Section 2: Classification
    print(f"\n📊 SECTION 2 — COLUMN CLASSIFICATION")
    for category, cols in report['classification'].items():
        print(f"  - {category}: {len(cols)}")

    # Section 2.5: Table Joins
    print(f"\n📊 SECTION 2.5 — TABLE JOINS")
    joins = report['table_joins']
    if joins:
        for foreign_table, details in joins.items():
            join_type = "✅ FK" if details['type'] == 'foreign_key' else "🔍 Potential"
            print(f"  {join_type} {table_name}.{details['join_column']} → {foreign_table}.{details['foreign_column']}")
    else:
        print(f"  ℹ️  No foreign key relationships detected")

    # Section 2.6: Column Usage
    print(f"\n📊 SECTION 2.6 — COLUMN USAGE (TOP 5)")
    usage_sorted = sorted(report['column_usage'].items(), key=lambda x: x[1]['usage_score'], reverse=True)
    for col, details in usage_sorted[:5]:
        print(f"  - {col}: {details['usage_score']} pts ({', '.join(details['reasons'])})")

    # Section 3: Core EDA
    print(f"\n📊 SECTION 3 — CORE EDA")
    print(f"\n  📈 Volume:")
    print(f"    - Total rows: {report['row_count']:,}")

    print(f"\n  🔍 Null Analysis (TOP 3):")
    for col, null_pct, null_count in report['null_percentages'][:3]:
        if null_pct > 0:
            icon = "🔴" if null_pct > 20 else "🟡" if null_pct > 5 else "🟢"
            print(f"    {icon} {col}: {null_pct:.1f}% null ({null_count:,} rows)")

    dup = report['dup_results']
    print(f"\n  🔑 Primary Key (sampled {dup['sample_size']:,} rows):")
    print(f"    - Unique keys : {dup['unique_keys']:,}")
    print(f"    - Duplicates  : {dup['duplicates']:,} ({dup['dup_pct']:.2f}%)")
    if dup['dup_pct'] > 0:
        print(f"    🔴 GRAIN VIOLATION detected")
    else:
        print(f"    🟢 VALID — No duplicates, grain is intact")

    # Section 4: Insights
    print(f"\n📊 SECTION 4 — KEY INSIGHTS")
    insights = []
    if report['row_count'] > 100_000_000:
        insights.append("🟡 Very high volume — performance considerations")
    elif report['row_count'] > 10_000_000:
        insights.append("🟡 High volume table — monitor performance")

    if len(report['schema_df']) > 200:
        insights.append("🔴 High complexity — consider denormalization")
    elif len(report['schema_df']) > 100:
        insights.append("🟡 Moderate complexity — good for analysis")

    if report['null_percentages']:
        top_col, top_pct, _ = report['null_percentages'][0]
        insights.append(f"🔴 High nulls: {top_col} ({top_pct:.1f}%)")

    if dup['dup_pct'] > 0:
        insights.append(f"🔴 Grain violation — {dup['dup_pct']:.2f}% PK duplicates")

    for insight in insights[:4]:
        print(f"  {insight}")

    # Section 5: Summary
    q = report['quality']
    print(f"\n📊 SECTION 5 — FINAL SUMMARY")
    print(f"\n  Table : {report['table_name']}")
    print(f"  Rows  : {report['row_count']:,} | Columns: {len(report['schema_df'])}")
    print(f"\n  📊 Data Quality Score: {q['score']}/100 ({q['quality_level']})")

    if q['risks']:
        print(f"\n  🚨 Key Risks:")
        for risk in q['risks'][:3]:
            print(f"    - {risk}")

    if q['recommendations']:
        print(f"\n  ✅ Recommendations:")
        for rec in q['recommendations'][:3]:
            print(f"    - {rec}")

    print(f"\n{SEP}")
    t = report['execution_time']
    print(f"⏱️  Execution Time: {t:.1f}s ({t / 60:.2f} min)")
    print(SEP)
    print("\n✅ EDA completed successfully!")
