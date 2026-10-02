from pathlib import Path
import sys

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# Project path
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


# ============================================================
# Text-to-SQL module
# ============================================================

from text_to_sql.sql_agent import ask_database


# ============================================================
# Llama 3.2
# ============================================================

llm = ChatOllama(
    model="llama3.2",
    temperature=0
)


# ============================================================
# Answer Generation Prompt
# ============================================================

ANSWER_PROMPT = """
You are NexusAI, an intelligent enterprise data assistant.

Your job is to convert database query results into a
clear natural-language business answer.

USER QUESTION:
{question}

GENERATED SQL:
{sql_query}

DATABASE RESULT:
{result}

RULES:

1. Answer ONLY using the database result provided above.
2. Never invent or assume values.
3. Do not calculate values that are not supported by the result.
4. If the result is empty, say that no matching data was found.
5. If the result contains INSUFFICIENT_DATA, clearly say that
   the requested information is not available in the database.
6. Do not mention internal implementation details unless useful.
7. Do not generate SQL.
8. Keep the answer concise and professional.
9. Include the important numerical values from the result.
10. NEVER add a currency symbol or currency name such as $, ₹, €,
    £, USD, INR, or dollars unless the database result explicitly
    contains the currency information.
11. Treat numeric values exactly as provided by the database.
12. If the question asks for a list, present the available
    values clearly.
13. If the result contains a single aggregate value, directly
    state the answer.
14. Do not add information that is not present in the database result.

Return only the final natural-language answer.
"""


# ============================================================
# Format Database Result
# ============================================================

def format_result(columns, rows):
    if not rows:
        return "No results found."

    result_lines = []

    for row in rows:
        row_data = []

        for column, value in zip(columns, row):
            row_data.append(
                f"{column}: {value}"
            )

        result_lines.append(
            " | ".join(row_data)
        )

    return "\n".join(result_lines)


# ============================================================
# Generate Natural Language Answer
# ============================================================

def generate_answer(question, sql_query, columns, rows):

    result_text = format_result(
        columns,
        rows
    )

    prompt = ChatPromptTemplate.from_template(
        ANSWER_PROMPT
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "question": question,
            "sql_query": sql_query,
            "result": result_text
        }
    )

    return response.content.strip()


# ============================================================
# Main Chat Function
# ============================================================

def ask_nexusai(question):

    if not question or not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    # Step 1:
    # Natural language -> SQL -> PostgreSQL
    sql_query, columns, rows = ask_database(
        question
    )

    # Step 2:
    # Database result -> Natural language answer
    answer = generate_answer(
        question,
        sql_query,
        columns,
        rows
    )

    return {
        "question": question,
        "sql": sql_query,
        "columns": columns,
        "rows": rows,
        "answer": answer
    }


# ============================================================
# CLI
# ============================================================

def main():

    print("\n========== NexusAI AI Chatbot ==========")
    print("\nDatabase : PostgreSQL")
    print("LLM      : Llama 3.2")
    print("Mode     : Text-to-SQL + AI Answer")
    print("\nType 'exit' to quit.")

    while True:

        question = input(
            "\nAsk NexusAI: "
        ).strip()

        if question.lower() == "exit":
            print("\nGoodbye!")
            break

        try:

            result = ask_nexusai(
                question
            )

            print("\n========== AI Answer ==========")
            print(result["answer"])

            print("\n========== Generated SQL ==========")
            print(result["sql"])

        except Exception as error:

            print(
                f"\nError: {error}"
            )


if __name__ == "__main__":
    main()