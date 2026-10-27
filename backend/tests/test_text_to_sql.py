import os
import sys
import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.text_to_sql import (
    process_chat_query,
    generate_sql_from_question,
    is_safe_sql,
    check_prompt_security,
    format_natural_language_answer
)


# -------------------------------------------------------------------------
# 1. Category Ranking (Lowest vs Highest, ASC vs DESC)
# -------------------------------------------------------------------------

def test_lowest_revenue_category_ranking(db_session, seeded_dataset):
    """
    Verify questions asking for lowest/least/bottom revenue generate
    correct ASC SQL and answer string specifying 'lowest'.
    """
    queries = [
        "Which category has the lowest revenue?",
        "Which category has the least revenue?",
        "What category had the lowest sales?",
        "Bottom category by revenue",
        "Lowest revenue category",
        "Tell me which category generated the minimum revenue"
    ]

    for q in queries:
        res = process_chat_query(db_session, q, dataset_id=seeded_dataset.id)
        sql = res["sql"].upper()
        answer = res["answer"]

        assert "ORDER BY" in sql
        assert "ASC" in sql
        assert "DESC" not in sql
        assert "lowest" in answer.lower()
        assert "highest" not in answer.lower()
        assert len(res["result"]) == 1
        assert "category" in res["result"][0]
        assert "total_revenue" in res["result"][0]


def test_highest_revenue_category_ranking(db_session, seeded_dataset):
    """
    Verify questions asking for highest/most/top revenue generate
    correct DESC SQL and answer string specifying 'highest'.
    """
    queries = [
        "Which category has the highest revenue?",
        "Which category generated the most revenue?",
        "Top category by revenue",
        "Highest revenue category",
        "What category has the largest sales?"
    ]

    for q in queries:
        res = process_chat_query(db_session, q, dataset_id=seeded_dataset.id)
        sql = res["sql"].upper()
        answer = res["answer"]

        assert "ORDER BY" in sql
        assert "DESC" in sql
        assert "highest" in answer.lower()
        assert len(res["result"]) == 1
        assert "category" in res["result"][0]
        assert "total_revenue" in res["result"][0]


def test_profit_and_expense_rankings(db_session, seeded_dataset):
    """Verify lowest/highest rankings for profit and expenses."""
    # Lowest profit
    res_low_prof = process_chat_query(db_session, "Which category has the smallest profit?", dataset_id=seeded_dataset.id)
    assert "ASC" in res_low_prof["sql"].upper()
    assert "lowest" in res_low_prof["answer"].lower() or "smallest" in res_low_prof["answer"].lower()
    assert "total_profit" in res_low_prof["sql"]

    # Highest profit
    res_high_prof = process_chat_query(db_session, "Which category has the largest profit?", dataset_id=seeded_dataset.id)
    assert "DESC" in res_high_prof["sql"].upper()
    assert "highest" in res_high_prof["answer"].lower()
    assert "total_profit" in res_high_prof["sql"]

    # Lowest expenses
    res_low_exp = process_chat_query(db_session, "Which category has the lowest expenses?", dataset_id=seeded_dataset.id)
    assert "ASC" in res_low_exp["sql"].upper()
    assert "lowest" in res_low_exp["answer"].lower()
    assert "total_expenses" in res_low_exp["sql"]

    # Highest expenses
    res_high_exp = process_chat_query(db_session, "Which category has the highest expenses?", dataset_id=seeded_dataset.id)
    assert "DESC" in res_high_exp["sql"].upper()
    assert "highest" in res_high_exp["answer"].lower()
    assert "total_expenses" in res_high_exp["sql"]


def test_multi_category_limit_rankings(db_session, seeded_dataset):
    """Verify parsing limits such as 'top 2' or 'bottom 2' categories."""
    res_top2 = process_chat_query(db_session, "Top 2 categories by revenue", dataset_id=seeded_dataset.id)
    assert "LIMIT 2" in res_top2["sql"].upper()
    assert "DESC" in res_top2["sql"].upper()
    assert len(res_top2["result"]) <= 2
    assert "top 2" in res_top2["answer"].lower()

    res_bot2 = process_chat_query(db_session, "Bottom 2 categories by revenue", dataset_id=seeded_dataset.id)
    assert "LIMIT 2" in res_bot2["sql"].upper()
    assert "ASC" in res_bot2["sql"].upper()
    assert len(res_bot2["result"]) <= 2
    assert "lowest 2" in res_bot2["answer"].lower()


# -------------------------------------------------------------------------
# 2. Aggregations, Synonyms, and Phrasing Variations
# -------------------------------------------------------------------------

def test_financial_aggregates_and_synonyms(db_session, seeded_dataset):
    """
    Verify flexible questions for total, average, and counts
    with synonyms (e.g. sales, earnings, expenditure, turnover).
    """
    # Total revenue synonyms
    q_rev = process_chat_query(db_session, "Calculate total sales", dataset_id=seeded_dataset.id)
    assert "SUM(revenue)" in q_rev["sql"]
    assert "The total revenue is" in q_rev["answer"]

    # Total profit synonyms
    q_prof = process_chat_query(db_session, "Find total net profit", dataset_id=seeded_dataset.id)
    assert "SUM(profit)" in q_prof["sql"]
    assert "The total profit is" in q_prof["answer"]

    # Total expenses synonyms
    q_exp = process_chat_query(db_session, "What is our total expenditure?", dataset_id=seeded_dataset.id)
    assert "SUM(expenses)" in q_exp["sql"]
    assert "The total expense is" in q_exp["answer"]

    # Averages
    q_avg_rev = process_chat_query(db_session, "What is the average revenue?", dataset_id=seeded_dataset.id)
    assert "AVG(revenue)" in q_avg_rev["sql"]
    assert "The average revenue is" in q_avg_rev["answer"]

    q_avg_exp = process_chat_query(db_session, "Calculate average expenses", dataset_id=seeded_dataset.id)
    assert "AVG(expenses)" in q_avg_exp["sql"]
    assert "The average expense is" in q_avg_exp["answer"]

    # Record counts
    q_cnt1 = process_chat_query(db_session, "How many records are available?", dataset_id=seeded_dataset.id)
    assert "COUNT(*)" in q_cnt1["sql"]
    assert "30 records available" in q_cnt1["answer"]

    q_cnt2 = process_chat_query(db_session, "Count all rows in this dataset", dataset_id=seeded_dataset.id)
    assert "COUNT(*)" in q_cnt2["sql"]
    assert "30 records available" in q_cnt2["answer"]


def test_financial_summary_and_breakdowns(db_session, seeded_dataset):
    """Verify summary and breakdown queries."""
    res_sum = process_chat_query(db_session, "Summarize financial performance", dataset_id=seeded_dataset.id)
    assert "SUM(revenue)" in res_sum["sql"]
    assert "SUM(expenses)" in res_sum["sql"]
    assert "SUM(profit)" in res_sum["sql"]
    assert "Financial Summary: Total Revenue =" in res_sum["answer"]
    assert "Net Margin:" in res_sum["answer"]

    res_compare = process_chat_query(db_session, "Compare revenue and expenses", dataset_id=seeded_dataset.id)
    assert "SUM(revenue)" in res_compare["sql"]

    res_cats = process_chat_query(db_session, "List all categories", dataset_id=seeded_dataset.id)
    assert "DISTINCT category" in res_cats["sql"]
    assert "Available categories" in res_cats["answer"]


# -------------------------------------------------------------------------
# 3. Security, Injection Blocking, and System Catalog Defense
# -------------------------------------------------------------------------

def test_sql_injection_defense(db_session):
    """Verify malicious prompts and SQL injection patterns are strictly blocked."""
    # Malicious prompt injection keywords
    bad_prompts = [
        "DROP TABLE finance_records;",
        "Which category has the lowest revenue?; DROP TABLE users;--",
        "DELETE FROM finance_records WHERE id > 0",
        "Show revenue UNION SELECT password FROM users",
        "SELECT * FROM finance_records WHERE 1=1; TRUNCATE TABLE datasets;",
        "What is the revenue? EXEC xp_cmdshell('dir')",
        "Show total profit; SHUTDOWN;"
    ]

    for bp in bad_prompts:
        is_safe, msg = check_prompt_security(bp)
        assert is_safe is False
        assert any(term in msg.lower() for term in ["security", "malicious", "forbidden", "illegal", "injection"])

        with pytest.raises(ValueError) as exc:
            process_chat_query(db_session, bp)
        assert any(term in str(exc.value).lower() for term in ["security", "malicious", "forbidden", "illegal", "injection"])


def test_table_and_column_allowlisting():
    """Verify query cannot access unauthorized tables or unauthorized columns."""
    # Unauthorized table
    safe1, msg1 = is_safe_sql("SELECT id, name FROM users")
    assert safe1 is False
    assert "users" in msg1

    safe2, msg2 = is_safe_sql("SELECT * FROM passwords")
    assert safe2 is False
    assert "passwords" in msg2

    # Unauthorized column on finance_records
    safe3, msg3 = is_safe_sql("SELECT secret_api_token FROM finance_records")
    assert safe3 is False
    assert "secret_api_token" in msg3 or "column" in msg3.lower()

    # System functions
    safe4, msg4 = is_safe_sql("SELECT pg_sleep(5) FROM finance_records")
    assert safe4 is False

    safe5, msg5 = is_safe_sql("SELECT version() FROM finance_records")
    assert safe5 is False


# -------------------------------------------------------------------------
# 4. Malformed Requests and Unsupported General Questions
# -------------------------------------------------------------------------

def test_unsupported_questions_return_informative_error(db_session):
    """
    Verify off-topic questions (weather, general trivia, poems)
    raise a clean ValueError explaining supported financial capabilities.
    """
    off_topic = [
        "What is the weather in New York?",
        "Can you write a poem about flowers?",
        "Who won the World Cup in 2022?",
        "Tell me a joke"
    ]

    for q in off_topic:
        with pytest.raises(ValueError) as exc:
            process_chat_query(db_session, q)
        assert "only answer questions related to your financial data" in str(exc.value).lower()


def test_empty_or_whitespace_questions_raise_error(db_session):
    """Verify empty or blank inputs are rejected gracefully."""
    with pytest.raises(ValueError) as exc1:
        process_chat_query(db_session, "")
    assert "empty" in str(exc1.value).lower()

    with pytest.raises(ValueError) as exc2:
        process_chat_query(db_session, "   ")
    assert "empty" in str(exc2.value).lower()
