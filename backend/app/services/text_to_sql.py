import os
import re
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.query_intent import (
    parse_intent_and_generate_sql,
    clean_text,
    detect_direction,
    Direction
)

ALLOWED_TABLES = {"finance_records", "datasets", "metadata"}

ALLOWED_COLUMNS = {
    # Base columns in finance_records
    "id", "dataset_id", "date", "category",
    "revenue", "expenses", "profit", "currency",
    "original_revenue", "original_expenses", "exchange_rate",
    # Aggregate aliases
    "total_revenue", "total_expenses", "total_profit",
    "avg_revenue", "avg_expenses", "avg_profit",
    "min_revenue", "min_expenses", "min_profit",
    "max_revenue", "max_expenses", "max_profit",
    "total_records", "count", "*"
}

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "SHUTDOWN",
    "INTO", "COPY", "LOCK", "CALL"
]

FORBIDDEN_FUNCTIONS = [
    "pg_sleep", "sleep", "benchmark", "pg_read_file", "pg_write_file",
    "pg_ls_dir", "dblink", "version", "current_user", "session_user",
    "current_database", "schema_name", "pg_tables"
]


def is_safe_sql(sql_query: str) -> Tuple[bool, str]:
    """
    Validate that the generated SQL query is strictly read-only, safe,
    and exclusively accesses allowed tables and columns.
    """
    if not sql_query or not sql_query.strip():
        return False, "SQL query cannot be empty."

    query_upper = sql_query.strip().upper()

    # Disallow SQL comments that could hide payload or confuse parsing
    if "--" in sql_query or "/*" in sql_query:
        return False, "SQL comments (-- or /* */) are not permitted."

    # Check for forbidden mutation/DDL keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(r'\b' + keyword + r'\b', query_upper):
            return False, f"Forbidden keyword detected: '{keyword}'. Only read-only SELECT operations are allowed."

    # Check for forbidden system functions
    for func in FORBIDDEN_FUNCTIONS:
        if re.search(r'\b' + func + r'\b', query_upper, re.IGNORECASE):
            return False, f"Forbidden system function detected: '{func}'."

    # Must start with SELECT or WITH
    if not (query_upper.startswith("SELECT") or query_upper.startswith("WITH")):
        return False, "Only SELECT or WITH queries are permitted."

    # Prevent multiple statements (semicolons)
    trimmed = query_upper.rstrip(';').strip()
    if ';' in trimmed:
        return False, "Multiple SQL statements are not permitted."

    # Validate table whitelist: inspect every table referenced after FROM or JOIN
    table_matches = re.findall(r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_".]+)', sql_query, re.IGNORECASE)
    if not table_matches:
        return False, "Query must specify a target table from the allowed tables list."

    for tbl in table_matches:
        clean_tbl = tbl.replace('"', '').split('.')[-1].lower()
        if clean_tbl not in ALLOWED_TABLES:
            return False, f"Access denied: table '{clean_tbl}' is not permitted. Allowed tables: {', '.join(sorted(ALLOWED_TABLES))}."

    # Validate column whitelist on the SELECT expression
    select_match = re.search(r'\bSELECT\s+(.*?)\s+\bFROM\b', sql_query, re.IGNORECASE | re.DOTALL)
    if select_match:
        select_expr = select_match.group(1).strip()
        # Strip leading DISTINCT keyword
        select_expr = re.sub(r'^\s*DISTINCT\s+', '', select_expr, flags=re.IGNORECASE)
        items = [it.strip() for it in select_expr.split(',')]
        for item in items:
            col_part = item
            if re.search(r'\bAS\b', col_part, re.IGNORECASE):
                col_part = re.split(r'\bAS\b', col_part, flags=re.IGNORECASE)[0].strip()

            func_match = re.search(
                r'\b(?:SUM|AVG|COUNT|MIN|MAX|DISTINCT|TRIM|ROUND|COALESCE)\s*\(\s*([a-zA-Z0-9_.*]+)\s*\)',
                col_part,
                re.IGNORECASE
            )
            if func_match:
                col_name = func_match.group(1).split('.')[-1].strip().lower()
            else:
                col_name = col_part.split('.')[-1].strip().lower()

            if col_name and col_name != "*" and col_name not in ALLOWED_COLUMNS:
                return False, f"Access denied: column '{col_name}' is not permitted. Allowed columns for financial queries."

    return True, "Safe"


def check_prompt_security(question: str) -> Tuple[bool, str]:
    """
    Validate natural language input prompt to prevent prompt injection or destructive requests.
    """
    if not question or not question.strip():
        return False, "Prompt cannot be empty."

    q_upper = question.upper()

    # Block destructive SQL injection keywords
    destructive_keywords = [
        "DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER",
        "GRANT", "REVOKE", "SHUTDOWN", "EXEC", "EXECUTE"
    ]
    for keyword in destructive_keywords:
        if re.search(r'\b' + keyword + r'\b', q_upper):
            return False, f"Malicious input detected: Attempting to perform illegal '{keyword}' operation."

    # Block DDL keywords
    if re.search(r'\bCREATE\s+(?:TABLE|DATABASE|INDEX|VIEW|USER|ROLE)\b', q_upper):
        return False, "Malicious input detected: Attempting to perform DDL CREATE operation."

    # Block explicit SQL injection syntax
    if re.search(r'(--|/\*|\*/|\bUNION\s+SELECT\b|\bUNION\s+ALL\s+SELECT\b|;\s*\w+)', q_upper):
        return False, "Security violation: SQL injection syntax detected in prompt."

    # Block forbidden system functions
    for func in FORBIDDEN_FUNCTIONS:
        if re.search(r'\b' + func + r'\b', q_upper, re.IGNORECASE):
            return False, f"Security violation: Reference to forbidden function '{func}'."

    return True, "Safe"


def generate_sql_from_question(
    question: str,
    dataset_id: Optional[int] = None
) -> Tuple[str, str, str, Dict[str, Any]]:
    """
    Generate a safe PostgreSQL/SQLite query from a natural language question.
    Uses LLM if API key is provided, or the robust semantic intent engine.
    Returns (sql_query, formatted_explanation, engine_type, intent_metadata).
    engine_type is either 'llm' or 'rule_engine'.
    """
    # Check if an LLM API key is present in environment
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if gemini_key:
        sql = _generate_sql_with_gemini(question, dataset_id, gemini_key)
        if sql and is_safe_sql(sql)[0]:
            return sql, "Generated via Gemini LLM", "llm", {"engine": "gemini"}
    elif openai_key:
        sql = _generate_sql_with_openai(question, dataset_id, openai_key)
        if sql and is_safe_sql(sql)[0]:
            return sql, "Generated via OpenAI LLM", "llm", {"engine": "openai"}

    # Robust semantic intent recognition engine (offline, deterministic, zero-dependency)
    sql, explanation, intent_meta = parse_intent_and_generate_sql(question, dataset_id)
    return sql, explanation, "rule_engine", intent_meta


def _generate_sql_with_gemini(question: str, dataset_id: Optional[int], api_key: str) -> Optional[str]:
    try:
        import urllib.request
        import json
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = f"""You are a PostgreSQL Text-to-SQL assistant for table 'finance_records'.
Table Schema:
- id (Integer)
- dataset_id (Integer)
- date (String)
- revenue (Float)
- expenses (Float)
- profit (Float)
- category (String)

Question: "{question}"
Dataset ID constraint: {dataset_id if dataset_id else 'None'}

Strict Rules:
1. Output ONLY valid PostgreSQL SQL query inside single line or clean string.
2. Do NOT use markdown ```sql codeblocks or extra text.
3. Use only SELECT statements on table 'finance_records'.
4. If dataset_id is provided ({dataset_id}), include `WHERE dataset_id = {dataset_id}`.
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_out = res_data['candidates'][0]['content']['parts'][0]['text']
            sql = text_out.strip().strip('`').replace('sql\n', '').strip()
            return sql
    except Exception:
        return None


def _generate_sql_with_openai(question: str, dataset_id: Optional[int], api_key: str) -> Optional[str]:
    try:
        import urllib.request
        import json
        url = "https://api.openai.com/v1/chat/completions"
        prompt = f"""You are a PostgreSQL Text-to-SQL assistant for table 'finance_records'.
Table Schema:
- id (Integer)
- dataset_id (Integer)
- date (String)
- revenue (Float)
- expenses (Float)
- profit (Float)
- category (String)

Question: "{question}"
Dataset ID constraint: {dataset_id if dataset_id else 'None'}

Strict Rules:
1. Output ONLY valid PostgreSQL SQL query.
2. Do NOT use markdown codeblocks.
3. Use only SELECT statements on table 'finance_records'.
4. If dataset_id is provided ({dataset_id}), include `WHERE dataset_id = {dataset_id}`.
"""
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            sql = res_data['choices'][0]['message']['content'].strip().strip('`').replace('sql\n', '').strip()
            return sql
    except Exception:
        return None


def format_natural_language_answer(
    question: str,
    sql_query: str,
    results: List[Dict[str, Any]],
    intent_meta: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format SQL query results into a clear, natural language explanation.
    Correctly recognizes ranking direction (highest vs lowest), aggregations,
    single vs multiple categories, and overall financial summaries.
    """
    if not results:
        return "No records were found in the database matching your request."

    first_row = results[0]
    sql_upper = sql_query.upper()
    q_cleaned = clean_text(question)

    # Check whether the query requested lowest / ascending order on primary metric
    is_ascending = False
    if intent_meta and intent_meta.get("direction"):
        is_ascending = intent_meta.get("direction") == "ASC"
    elif re.search(r'ORDER\s+BY\s+(?:total_\w+|\w+)\s+ASC\b', sql_upper):
        is_ascending = True
    elif detect_direction(q_cleaned) == Direction.ASC:
        is_ascending = True

    # 1. Distinct categories list
    if (intent_meta and intent_meta.get("intent") == "distinct_categories") or (len(first_row) == 1 and "category" in first_row and len(results) > 1):
        cats = [str(r["category"]) for r in results if r.get("category")]
        return f"Available categories ({len(cats)}): {', '.join(cats)}."

    # 2. Overall Financial Summary (total_revenue, total_expenses, total_profit)
    if "total_revenue" in first_row and "total_expenses" in first_row and "total_profit" in first_row:
        rev = first_row.get("total_revenue", 0) or 0
        exp = first_row.get("total_expenses", 0) or 0
        prof = first_row.get("total_profit", 0) or 0
        margin = (prof / rev * 100) if rev else 0.0
        return (
            f"Financial Summary: Total Revenue = ${rev:,.2f}, "
            f"Total Expenses = ${exp:,.2f}, Total Profit = ${prof:,.2f} "
            f"(Net Margin: {margin:.1f}%)."
        )

    # 3. Category rankings or breakdowns (e.g., category + metric)
    if "category" in first_row and any(k.startswith("total_") for k in first_row.keys()):
        # Determine the metric name
        metric_key = next((k for k in first_row.keys() if k.startswith("total_")), "total_revenue")
        metric_name = metric_key.replace("total_", "")  # 'revenue', 'profit', 'expenses'

        dir_label = "lowest" if is_ascending else "highest"

        # Single category ranking
        if len(results) == 1:
            cat = first_row.get("category", "N/A")
            amt = first_row.get(metric_key, 0) or 0
            amt_str = f"${amt:,.2f}" if isinstance(amt, (int, float)) else str(amt)
            return f"The category with the {dir_label} {metric_name} is '{cat}' with a total {metric_name} of {amt_str}."

        # Multiple categories ranking / breakdown
        rank_label = "lowest" if is_ascending else "top"
        lines = [f"The {rank_label} {len(results)} categories by {metric_name} are:"]
        for idx, row in enumerate(results, start=1):
            cat = row.get("category", "N/A")
            amt = row.get(metric_key, 0) or 0
            lines.append(f"{idx}. '{cat}': ${amt:,.2f}")
        return "\n".join(lines)

    # 4. Single aggregated metric value (len(results) == 1 and len(first_row) == 1)
    if len(results) == 1 and len(first_row) == 1:
        key, val = list(first_row.items())[0]
        val_str = f"${val:,.2f}" if isinstance(val, (int, float)) and "count" not in key.lower() and "records" not in key.lower() else str(val)

        # Average / Mean metrics
        if "avg" in key.lower() or "mean" in key.lower() or "average" in question.lower():
            if "revenue" in key.lower() or "revenue" in question.lower():
                return f"The average revenue is {val_str}."
            elif "profit" in key.lower() or "profit" in question.lower():
                return f"The average profit is {val_str}."
            elif "expense" in key.lower() or "expense" in question.lower():
                return f"The average expense is {val_str}."
            else:
                return f"The average {key.replace('_', ' ')} is {val_str}."

        # Total / Sum metrics
        if "revenue" in key.lower():
            return f"The total revenue is {val_str}."
        elif "profit" in key.lower():
            return f"The total profit is {val_str}."
        elif "expense" in key.lower():
            return f"The total expense is {val_str}."
        elif "count" in key.lower() or "records" in key.lower():
            return f"There are {val} records available in the database."
        else:
            return f"The calculated {key.replace('_', ' ')} is {val_str}."

    # 5. Multiple records view (sample rows)
    if len(results) > 1 and "date" in first_row:
        return f"Retrieved {len(results)} records from the dataset."

    items_summary = ", ".join([f"{k}: {v}" for k, v in first_row.items()])
    return f"Here is the result for your request: {items_summary}."


def process_chat_query(db: Session, question: str, dataset_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Main Text-to-SQL pipeline:
    1. Validates prompt security.
    2. Generates SQL query from question.
    3. Validates SQL query security (Table & Column whitelist, read-only SELECT).
    4. Executes query safely against database session with statement timeout.
    5. Formats natural-language answer.
    """
    if not question or not question.strip():
        raise ValueError("Question string cannot be empty.")

    # 1. Prompt security check
    prompt_safe, prompt_msg = check_prompt_security(question)
    if not prompt_safe:
        raise ValueError(f"Security Violation: {prompt_msg}")

    # 2. Generate SQL
    sql_query, explanation, engine_type, intent_meta = generate_sql_from_question(question, dataset_id)

    # 3. Validate SQL against table whitelist and syntax safety
    is_safe, safety_msg = is_safe_sql(sql_query)
    if not is_safe:
        raise ValueError(f"SQL Security Violation: {safety_msg}")

    # 4. Execute SQL safely with statement timeout
    try:
        # Enforce PostgreSQL statement timeout where supported
        try:
            if db.bind and db.bind.dialect.name == "postgresql":
                db.execute(text("SET LOCAL statement_timeout = '5000ms';"))
        except Exception:
            pass

        statement = text(sql_query)
        res = db.execute(statement)

        keys = res.keys()
        rows = res.fetchall()

        results_list = []
        for r in rows:
            row_dict = {}
            for i, key in enumerate(keys):
                val = r[i]
                if isinstance(val, float):
                    val = round(val, 2)
                row_dict[key] = val
            results_list.append(row_dict)

        # 5. Format natural language answer
        answer = format_natural_language_answer(question, sql_query, results_list, intent_meta)

        return {
            "question": question,
            "sql": sql_query,
            "result": results_list,
            "answer": answer,
            "engine": engine_type,
            "explanation": explanation
        }

    except Exception as db_err:
        raise RuntimeError(f"Database query execution error: {str(db_err)}")
