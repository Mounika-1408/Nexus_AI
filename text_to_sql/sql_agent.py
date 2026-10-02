from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from text_to_sql.db import execute_query, get_schema


# ============================================================
# LLM
# ============================================================

llm = ChatOllama(
    model="llama3.2",
    temperature=0
)


# ============================================================
# Text-to-SQL Prompt
# ============================================================

SQL_PROMPT = """
You are the Text-to-SQL engine for NexusAI.

Convert the user's natural-language question into a
PostgreSQL SQL query.

DATABASE SCHEMA:

{schema}

RULES:

1. Generate ONLY one SELECT query.
2. Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
   CREATE, TRUNCATE, GRANT, REVOKE, or other write queries.
3. Use ONLY tables and columns present in the schema.
4. Never invent tables or columns.
5. Use PostgreSQL syntax.
6. Do not use markdown.
7. Do not include explanations.
8. Return ONLY the SQL query.
9. Use JOIN when information from multiple related tables
   is required.
10. Use aggregate functions such as COUNT, SUM, AVG, MIN,
    and MAX when appropriate.
11. If the question cannot be answered using the available
    schema, return:
    SELECT 'INSUFFICIENT_DATA' AS message;

USER QUESTION:

{question}
"""


# ============================================================
# Build Schema Text
# ============================================================

def build_schema_text():

    schema = get_schema()

    if not schema:
        raise ValueError(
            "No database tables were found."
        )

    schema_text = ""

    for table_name, columns in schema.items():

        schema_text += (
            f"Table: {table_name}\n"
        )

        for column in columns:

            schema_text += (
                f"  - {column['column']} "
                f"({column['type']})\n"
            )

        schema_text += "\n"

    return schema_text


# ============================================================
# Generate SQL
# ============================================================

def generate_sql(question):

    if not question or not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    schema_text = build_schema_text()

    prompt = ChatPromptTemplate.from_template(
        SQL_PROMPT
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "schema": schema_text,
            "question": question
        }
    )

    sql_query = response.content.strip()

    # Remove markdown if LLM adds it
    sql_query = (
        sql_query
        .replace("```sql", "")
        .replace("```postgresql", "")
        .replace("```", "")
        .strip()
    )

    return sql_query


# ============================================================
# Validate SQL
# ============================================================

def validate_sql(sql_query):

    query = sql_query.strip()

    if not query:
        raise ValueError(
            "Generated SQL is empty."
        )

    # Only one statement
    if ";" in query.rstrip(";"):
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

    # Must start with SELECT
    if not query.lower().startswith("select"):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    forbidden_keywords = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "truncate",
        "grant",
        "revoke"
    ]

    normalized_query = query.lower()

    for keyword in forbidden_keywords:

        if keyword in normalized_query:

            raise ValueError(
                f"Unsafe SQL detected: {keyword}"
            )

    return True


# ============================================================
# Ask Database
# ============================================================

def ask_database(question):

    sql_query = generate_sql(question)

    validate_sql(sql_query)

    print("\n========== Generated SQL ==========")
    print(sql_query)

    columns, rows = execute_query(
        sql_query
    )

    return sql_query, columns, rows


# ============================================================
# Display Results
# ============================================================

def display_results(columns, rows):

    print("\n========== Query Result ==========")

    if not rows:

        print("No results found.")

        return

    print(
        " | ".join(
            str(column)
            for column in columns
        )
    )

    print("-" * 80)

    for row in rows:

        print(
            " | ".join(
                str(value)
                for value in row
            )
        )


# ============================================================
# Main
# ============================================================

def main():

    print(
        "\n========== NexusAI Text-to-SQL =========="
    )

    print(
        "\nConnected database: nexus_ai"
    )

    print(
        "Model: Llama 3.2"
    )

    print(
        "\nType 'exit' to quit."
    )

    while True:

        question = input(
            "\nAsk a database question: "
        )

        if question.lower().strip() == "exit":

            print("\nGoodbye!")

            break

        try:

            sql_query, columns, rows = (
                ask_database(question)
            )

            display_results(
                columns,
                rows
            )

        except Exception as error:

            print(
                f"\nError: {error}"
            )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()