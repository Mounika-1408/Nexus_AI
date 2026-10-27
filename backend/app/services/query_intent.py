"""
NexusAI Query Intent Recognition and SQL Generator.
Translates generalized natural language questions into safe, deterministic SQL queries
targeting the 'finance_records' schema without requiring external LLM dependencies.
"""

import re
from typing import Optional, Tuple, Dict, Any, List
from enum import Enum


class Metric(str, Enum):
    REVENUE = "revenue"
    PROFIT = "profit"
    EXPENSES = "expenses"
    RECORDS = "records"


class Direction(str, Enum):
    ASC = "ASC"    # lowest, least, bottom, smallest, minimum, worst
    DESC = "DESC"  # highest, most, top, largest, maximum, best


class Aggregation(str, Enum):
    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"


# Synonyms mapping to canonical metrics
METRIC_SYNONYMS: Dict[Metric, List[str]] = {
    Metric.REVENUE: [
        "revenue", "revenues", "rev", "sales", "sale",
        "turnover", "gross income", "gross revenue", "gross"
    ],
    Metric.PROFIT: [
        "profit", "profits", "margin", "margins", "net income",
        "net profit", "profitable", "profitability", "gain", "gains", "earnings"
    ],
    Metric.EXPENSES: [
        "expense", "expenses", "expenditure", "expenditures",
        "cost", "costs", "spend", "spending", "outgoings", "spent"
    ],
    Metric.RECORDS: [
        "record", "records", "rows", "row", "entries", "entry",
        "items", "count", "transactions", "data points"
    ]
}

# Direction keywords
ASCENDING_KEYWORDS = [
    "lowest", "least", "bottom", "smallest", "minimum", "min",
    "worst", "poorest", "fewest", "cheapest", "lower", "lesser", "underperforming"
]

DESCENDING_KEYWORDS = [
    "highest", "most", "top", "largest", "biggest", "maximum", "max",
    "best", "greatest", "leading", "higher", "greater"
]

# Aggregation keywords
AVERAGE_KEYWORDS = ["average", "avg", "mean", "per record", "typically", "per row"]
COUNT_KEYWORDS = ["how many", "count", "number of", "total number", "amount of records", "quantity"]

# Category keywords
CATEGORY_KEYWORDS = [
    "category", "categories", "department", "departments",
    "segment", "segments", "sector", "sectors", "type", "types",
    "product line", "product lines", "class", "classes"
]

# Summary keywords
SUMMARY_KEYWORDS = [
    "summary", "overview", "kpi", "kpis", "financial health",
    "performance", "all metrics", "financial metrics", "dashboard",
    "financials", "overall status"
]


def clean_text(text: str) -> str:
    """Normalize question text for robust regex token matching."""
    text = text.lower().strip()
    # Replace non-alphanumeric (except underscores, spaces, hyphens) with space
    text = re.sub(r"[^\w\s-]", " ", text)
    # Collapse multiple whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_metric(cleaned_text: str) -> Optional[Metric]:
    """Identify the primary financial metric referenced in the question."""
    # Check multi-word synonyms first
    for metric, synonyms in METRIC_SYNONYMS.items():
        for syn in synonyms:
            if " " in syn and re.search(r"\b" + re.escape(syn) + r"\b", cleaned_text):
                return metric

    # Check single-word synonyms
    for metric, synonyms in METRIC_SYNONYMS.items():
        for syn in synonyms:
            if " " not in syn and re.search(r"\b" + re.escape(syn) + r"\b", cleaned_text):
                return metric

    return None


def detect_direction(cleaned_text: str) -> Optional[Direction]:
    """Detect ranking direction (ASC vs DESC) from synonyms."""
    for kw in ASCENDING_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", cleaned_text):
            return Direction.ASC

    for kw in DESCENDING_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", cleaned_text):
            return Direction.DESC

    return None


def detect_limit(cleaned_text: str, default: int = 1) -> int:
    """Extract numeric limit (e.g. 'top 3', 'bottom 5', '10 lowest'). Clamped between 1 and 50."""
    # Pattern: keyword followed by number: 'top 5', 'bottom 3', 'lowest 10'
    match = re.search(r"\b(?:top|bottom|lowest|highest|first|last|least|most)\s+(\d+)\b", cleaned_text)
    if match:
        val = int(match.group(1))
        return max(1, min(50, val))

    # Pattern: number followed by keyword: '5 highest', '3 bottom'
    match2 = re.search(r"\b(\d+)\s+(?:top|bottom|lowest|highest|first|last|least|most)\b", cleaned_text)
    if match2:
        val = int(match2.group(1))
        return max(1, min(50, val))

    # If plural 'categories' or 'top categories' without number, return 5
    if any(re.search(r"\b" + re.escape(p) + r"\b", cleaned_text) for p in ["categories", "rankings", "breakdown"]):
        return 5

    return default


def parse_intent_and_generate_sql(
    question: str,
    dataset_id: Optional[int] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Parse natural language question using semantic intent recognition and generate safe SQL.
    Returns (sql_query, explanation, intent_metadata).
    Raises ValueError if question cannot be mapped to any supported financial intent.
    """
    cleaned = clean_text(question)

    if not cleaned:
        raise ValueError("Question string cannot be empty.")

    # Base WHERE clause for dataset scoping
    ds_filter = f"dataset_id = {int(dataset_id)}" if dataset_id is not None else None

    def build_where(extra_conditions: Optional[List[str]] = None) -> str:
        conds = []
        if ds_filter:
            conds.append(ds_filter)
        if extra_conditions:
            conds.extend(extra_conditions)
        return f"WHERE {' AND '.join(conds)}" if conds else ""

    metric = detect_metric(cleaned)
    direction = detect_direction(cleaned)
    limit = detect_limit(cleaned, default=1)

    has_category = any(re.search(r"\b" + re.escape(k) + r"\b", cleaned) for k in CATEGORY_KEYWORDS)
    is_ranking_question = direction is not None or any(
        re.search(r"\b" + re.escape(w) + r"\b", cleaned)
        for w in ["which", "what category", "who", "rank", "ranking", "rankings", "leader"]
    )
    is_average = any(re.search(r"\b" + re.escape(w) + r"\b", cleaned) for w in AVERAGE_KEYWORDS)
    is_count = metric == Metric.RECORDS or any(re.search(r"\b" + re.escape(w) + r"\b", cleaned) for w in COUNT_KEYWORDS)
    is_summary = any(re.search(r"\b" + re.escape(w) + r"\b", cleaned) for w in SUMMARY_KEYWORDS)
    is_compare = any(re.search(r"\b" + re.escape(w) + r"\b", cleaned) for w in ["compare", "comparison", "vs", "versus"])
    is_list_categories = has_category and any(
        re.search(r"\b" + re.escape(w) + r"\b", cleaned)
        for w in ["list", "show", "all", "what are", "available", "distinct", "unique"]
    ) and not direction and not metric

    is_sample_records = any(
        re.search(r"\b" + re.escape(w) + r"\b", cleaned)
        for w in ["all records", "show records", "show data", "sample data", "sample records", "view records", "display data"]
    )

    # 1. Distinct categories list
    if is_list_categories:
        where = build_where(["category IS NOT NULL", "TRIM(category) != ''"])
        sql = f"SELECT DISTINCT category FROM finance_records {where} ORDER BY category ASC"
        return re.sub(r"\s+", " ", sql).strip(), "Extracted unique categories list", {
            "intent": "distinct_categories"
        }

    # 2. Sample records view
    if is_sample_records and not metric and not direction:
        rec_limit = min(limit if limit > 1 else 10, 50)
        where = build_where()
        sql = f"SELECT id, date, category, revenue, expenses, profit FROM finance_records {where} ORDER BY id ASC LIMIT {rec_limit}"
        return re.sub(r"\s+", " ", sql).strip(), f"Retrieved {rec_limit} sample records", {
            "intent": "sample_records", "limit": rec_limit
        }

    # 3. Category Ranking (Highest / Lowest / Top / Bottom / Most / Least / Smallest / Largest)
    # Triggers if a direction is detected AND (category is mentioned OR ranking question structure)
    if (direction is not None and (has_category or is_ranking_question or metric is not None)) or (has_category and is_ranking_question):
        # Default metric to revenue if not explicitly stated (e.g. "which category has the lowest?" or "top 3 categories")
        target_metric = metric.value if metric and metric != Metric.RECORDS else "revenue"
        col_name = target_metric
        agg_alias = f"total_{target_metric}"

        sort_dir = direction.value if direction else "DESC"
        rec_limit = limit

        where = build_where(["category IS NOT NULL", "TRIM(category) != ''"])
        sql = (
            f"SELECT category, SUM({col_name}) AS {agg_alias} "
            f"FROM finance_records {where} "
            f"GROUP BY category "
            f"ORDER BY {agg_alias} {sort_dir}, category ASC "
            f"LIMIT {rec_limit}"
        )
        explanation = f"Ranked categories by {target_metric} in {sort_dir} order (limit {rec_limit})"
        return re.sub(r"\s+", " ", sql).strip(), explanation, {
            "intent": "category_ranking",
            "metric": target_metric,
            "direction": sort_dir,
            "limit": rec_limit
        }

    # 4. Category breakdown / grouping without explicit ranking direction (e.g., "show revenue by category")
    if has_category and metric and metric != Metric.RECORDS and any(
        re.search(r"\b" + re.escape(w) + r"\b", cleaned)
        for w in ["by", "per", "breakdown", "each", "group", "grouped", "across"]
    ):
        target_metric = metric.value
        col_name = target_metric
        agg_alias = f"total_{target_metric}"
        rec_limit = min(limit if limit > 1 else 10, 50)
        where = build_where(["category IS NOT NULL", "TRIM(category) != ''"])
        sql = (
            f"SELECT category, SUM({col_name}) AS {agg_alias} "
            f"FROM finance_records {where} "
            f"GROUP BY category "
            f"ORDER BY {agg_alias} DESC, category ASC "
            f"LIMIT {rec_limit}"
        )
        return re.sub(r"\s+", " ", sql).strip(), f"Calculated {target_metric} grouped by category", {
            "intent": "category_breakdown", "metric": target_metric, "limit": rec_limit
        }

    # 5. Count / Number of records
    if is_count:
        where = build_where()
        sql = f"SELECT COUNT(*) AS total_records FROM finance_records {where}"
        return re.sub(r"\s+", " ", sql).strip(), "Counted total finance records", {
            "intent": "record_count"
        }

    # 6. Overall Financial Summary / Compare
    if is_summary or is_compare:
        where = build_where()
        sql = (
            f"SELECT SUM(revenue) AS total_revenue, "
            f"SUM(expenses) AS total_expenses, "
            f"SUM(profit) AS total_profit "
            f"FROM finance_records {where}"
        )
        return re.sub(r"\s+", " ", sql).strip(), "Aggregated overall financial performance indicators", {
            "intent": "financial_summary"
        }

    # 7. Average / Mean calculation
    if is_average:
        target_metric = metric.value if metric and metric != Metric.RECORDS else "revenue"
        agg_alias = f"avg_{target_metric}"
        where = build_where()
        sql = f"SELECT AVG({target_metric}) AS {agg_alias} FROM finance_records {where}"
        return re.sub(r"\s+", " ", sql).strip(), f"Calculated average {target_metric}", {
            "intent": "aggregate_metric", "aggregation": "AVG", "metric": target_metric
        }

    # 8. Single aggregate sum for metric (revenue, profit, expenses)
    if metric and metric != Metric.RECORDS:
        target_metric = metric.value
        agg_alias = f"total_{target_metric}"
        where = build_where()
        sql = f"SELECT SUM({target_metric}) AS {agg_alias} FROM finance_records {where}"
        return re.sub(r"\s+", " ", sql).strip(), f"Calculated total {target_metric}", {
            "intent": "aggregate_metric", "aggregation": "SUM", "metric": target_metric
        }

    # 9. General financial terms fallback (e.g. "sales data", "finance figures")
    if any(re.search(r"\b" + re.escape(w) + r"\b", cleaned) for w in ["finance", "financial", "figures", "data", "stats", "kpi"]):
        where = build_where()
        sql = (
            f"SELECT SUM(revenue) AS total_revenue, "
            f"SUM(expenses) AS total_expenses, "
            f"SUM(profit) AS total_profit "
            f"FROM finance_records {where}"
        )
        return re.sub(r"\s+", " ", sql).strip(), "Generated financial KPI summary", {
            "intent": "financial_summary"
        }

    # If no recognized intent matched, raise a clear informative ValueError
    raise ValueError(
        "I can only answer questions related to your financial data "
        "(such as revenue, profit, expenses, category rankings, summary metrics, and record counts). "
        "Try asking: 'Which category has the lowest revenue?', 'What is the total profit?', "
        "or 'Top 3 categories by sales'."
    )
