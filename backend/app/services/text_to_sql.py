import os
import re
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import text

ALLOWED_TABLES = {"finance_records", "datasets", "companies", "metadata"}
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "SHUTDOWN"
]

def is_safe_sql(sql_query: str) -> Tuple[bool, str]:
    """
    Validate that the generated SQL query is strictly read-only and safe to execute.
    """
    query_upper = sql_query.strip().upper()

    if not query_upper:
        return False, "SQL query cannot be empty."

    # Check for forbidden mutation/DDL keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(r'\b' + keyword + r'\b', query_upper):
            return False, f"Forbidden keyword detected: {keyword}. Only SELECT operations are allowed."

    # Must start with SELECT or WITH
    if not (query_upper.startswith("SELECT") or query_upper.startswith("WITH")):
        return False, "Only SELECT or WITH queries are permitted."

    # Prevent multiple statements (semicolons)
    trimmed = query_upper.rstrip(';').strip()
    if ';' in trimmed:
        return False, "Multiple SQL statements are not permitted."

    return True, "Safe"


def check_prompt_security(question: str) -> Tuple[bool, str]:
    """
    Validate natural language input prompt to prevent SQL injection or malicious instructions.
    """
    q_upper = question.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(r'\b' + keyword + r'\b', q_upper):
            return False, f"Malicious input detected: Attempting to perform illegal '{keyword}' operation."
    return True, "Safe"


def generate_sql_from_question(question: str, dataset_id: Optional[int] = None) -> Tuple[str, str]:
    """
    Generate a safe PostgreSQL query from a natural language question.
    Uses LLM if API key is provided, or a robust semantic pattern translator.
    Returns (sql_query, formatted_explanation).
    """
    q_lower = question.lower().strip()
    where_clause = f"WHERE dataset_id = {int(dataset_id)}" if dataset_id is not None else ""

    # Check if an LLM API key is present in environment
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if gemini_key:
        sql = _generate_sql_with_gemini(question, dataset_id, gemini_key)
        if sql:
            return sql, "Generated via Gemini LLM"
    elif openai_key:
        sql = _generate_sql_with_openai(question, dataset_id, openai_key)
        if sql:
            return sql, "Generated via OpenAI LLM"

    # Pattern-based SQL translation engine (guaranteed offline fallback)
    if "total revenue" in q_lower or ("sum" in q_lower and "revenue" in q_lower):
        sql = f"SELECT SUM(revenue) AS total_revenue FROM finance_records {where_clause}".strip()
    elif "total profit" in q_lower or ("sum" in q_lower and "profit" in q_lower):
        sql = f"SELECT SUM(profit) AS total_profit FROM finance_records {where_clause}".strip()
    elif "total expenses" in q_lower or "total expense" in q_lower or ("sum" in q_lower and "expense" in q_lower):
        sql = f"SELECT SUM(expenses) AS total_expenses FROM finance_records {where_clause}".strip()
    elif "how many" in q_lower or "count" in q_lower or "total records" in q_lower or "number of records" in q_lower:
        sql = f"SELECT COUNT(*) AS total_records FROM finance_records {where_clause}".strip()
    elif "highest revenue" in q_lower or "top category" in q_lower or "top categories" in q_lower or "most revenue" in q_lower:
        limit_match = re.search(r'top\s+(\d+)', q_lower)
        limit = limit_match.group(1) if limit_match else "1"
        sql = f"SELECT category, SUM(revenue) AS total_revenue FROM finance_records {where_clause} GROUP BY category ORDER BY total_revenue DESC LIMIT {limit}".strip()
    elif "highest profit" in q_lower or "most profitable" in q_lower:
        limit_match = re.search(r'top\s+(\d+)', q_lower)
        limit = limit_match.group(1) if limit_match else "1"
        sql = f"SELECT category, SUM(profit) AS total_profit FROM finance_records {where_clause} GROUP BY category ORDER BY total_profit DESC LIMIT {limit}".strip()
    elif "highest expense" in q_lower or "highest expenses" in q_lower or "most expense" in q_lower:
        limit_match = re.search(r'top\s+(\d+)', q_lower)
        limit = limit_match.group(1) if limit_match else "1"
        sql = f"SELECT category, SUM(expenses) AS total_expenses FROM finance_records {where_clause} GROUP BY category ORDER BY total_expenses DESC LIMIT {limit}".strip()
    elif "average revenue" in q_lower or "avg revenue" in q_lower:
        sql = f"SELECT AVG(revenue) AS avg_revenue FROM finance_records {where_clause}".strip()
    elif "average profit" in q_lower or "avg profit" in q_lower:
        sql = f"SELECT AVG(profit) AS avg_profit FROM finance_records {where_clause}".strip()
    elif "category" in q_lower and ("list" in q_lower or "show" in q_lower or "all" in q_lower):
        sql = f"SELECT DISTINCT category FROM finance_records {where_clause}".strip()
    elif "all records" in q_lower or "show records" in q_lower or "show data" in q_lower:
        sql = f"SELECT id, date, category, revenue, expenses, profit FROM finance_records {where_clause} ORDER BY id ASC LIMIT 10".strip()
    else:
        sql = f"SELECT SUM(revenue) AS total_revenue, SUM(expenses) AS total_expenses, SUM(profit) AS total_profit FROM finance_records {where_clause}".strip()

    sql = re.sub(r'\s+', ' ', sql).strip()
    return sql, "Generated via NexusAI Text-to-SQL Engine"


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
3. Use only SELECT statements.
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
3. Use only SELECT statements.
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


def format_natural_language_answer(question: str, sql_query: str, results: List[Dict[str, Any]]) -> str:
    if not results:
        return "No records were found in the database matching your request."

    first_row = results[0]

    if len(results) == 1 and len(first_row) == 1:
        key, val = list(first_row.items())[0]
        val_str = f"${val:,.2f}" if isinstance(val, (int, float)) and "count" not in key.lower() else str(val)
        
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

    if "category" in first_row and ("total_revenue" in first_row or "total_profit" in first_row or "total_expenses" in first_row):
        cat = first_row.get("category", "N/A")
        if "total_revenue" in first_row:
            amt = first_row["total_revenue"]
            return f"The category with the highest revenue is '{cat}' with a total revenue of ${amt:,.2f}."
        elif "total_profit" in first_row:
            amt = first_row["total_profit"]
            return f"The category with the highest profit is '{cat}' with a total profit of ${amt:,.2f}."
        elif "total_expenses" in first_row:
            amt = first_row["total_expenses"]
            return f"The category with the highest expenses is '{cat}' with total expenses of ${amt:,.2f}."

    if "total_revenue" in first_row and "total_expenses" in first_row and "total_profit" in first_row:
        rev = first_row.get("total_revenue", 0) or 0
        exp = first_row.get("total_expenses", 0) or 0
        prof = first_row.get("total_profit", 0) or 0
        return f"Financial Summary: Total Revenue = ${rev:,.2f}, Total Expenses = ${exp:,.2f}, Total Profit = ${prof:,.2f}."

    items_summary = ", ".join([f"{k}: {v}" for k, v in first_row.items()])
    return f"Here is the result for your request: {items_summary}."


def process_chat_query(db: Session, question: str, dataset_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Main Text-to-SQL pipeline:
    1. Validates prompt security.
    2. Generates SQL query from question.
    3. Validates SQL query security (Read-only SELECT).
    4. Executes query safely against PostgreSQL session.
    5. Formats natural-language answer.
    """
    if not question or not question.strip():
        raise ValueError("Question string cannot be empty.")

    # 1. Prompt security check
    prompt_safe, prompt_msg = check_prompt_security(question)
    if not prompt_safe:
        raise ValueError(f"Security Violation: {prompt_msg}")

    # 2. Generate SQL
    sql_query, engine_type = generate_sql_from_question(question, dataset_id)

    # 3. Validate SQL
    is_safe, safety_msg = is_safe_sql(sql_query)
    if not is_safe:
        raise ValueError(f"SQL Security Violation: {safety_msg}")

    # 4. Execute SQL
    try:
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
        answer = format_natural_language_answer(question, sql_query, results_list)

        return {
            "question": question,
            "sql": sql_query,
            "result": results_list,
            "answer": answer
        }

    except Exception as db_err:
        raise RuntimeError(f"Database query execution error: {str(db_err)}")
