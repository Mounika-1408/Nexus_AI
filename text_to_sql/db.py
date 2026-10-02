import os

from sqlalchemy import create_engine, text


# ============================================================
# PostgreSQL Configuration
# ============================================================

DB_HOST = os.getenv(
    "NEXUSAI_DB_HOST",
    "192.168.29.113"
)

DB_PORT = os.getenv(
    "NEXUSAI_DB_PORT",
    "5432"
)

DB_NAME = os.getenv(
    "NEXUSAI_DB_NAME",
    "nexus_ai"
)

DB_USER = os.getenv(
    "NEXUSAI_DB_USER",
    "postgres"
)

DB_PASSWORD = os.getenv(
    "NEXUSAI_DB_PASSWORD"
)


# ============================================================
# Database Connection
# ============================================================

if not DB_PASSWORD:
    raise RuntimeError(
        "NEXUSAI_DB_PASSWORD environment variable is not set."
    )


DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# ============================================================
# Test Connection
# ============================================================

def test_connection():

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT 1")
            )

            result.fetchone()

        print("PostgreSQL connection successful.")

        return True

    except Exception as error:

        print("PostgreSQL connection failed.")
        print(f"Error: {error}")

        return False


# ============================================================
# Execute Query
# ============================================================

def execute_query(query):

    with engine.connect() as connection:

        result = connection.execute(
            text(query)
        )

        rows = result.fetchall()
        columns = result.keys()

        return columns, rows


# ============================================================
# Get Database Schema
# ============================================================

def get_schema():

    query = """
    SELECT
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY
        table_name,
        ordinal_position;
    """

    columns, rows = execute_query(query)

    schema = {}

    for table_name, column_name, data_type in rows:

        if table_name not in schema:
            schema[table_name] = []

        schema[table_name].append(
            {
                "column": column_name,
                "type": data_type
            }
        )

    return schema


# ============================================================
# Print Database Schema
# ============================================================

def print_schema():

    schema = get_schema()

    print("\n========== Database Schema ==========\n")

    if not schema:

        print("No tables found.")

        return

    for table_name, columns in schema.items():

        print(f"Table: {table_name}")

        for column in columns:

            print(
                f"  - {column['column']} "
                f"({column['type']})"
            )

        print()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    if test_connection():

        print_schema()