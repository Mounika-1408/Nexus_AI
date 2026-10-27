import os
import sys
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.models.user import User
from app.services.text_to_sql import is_safe_sql, process_chat_query, check_prompt_security
from app.services.auth_service import hash_password, verify_password


@pytest.fixture
def client():
    return TestClient(app)


def test_password_hashing():
    """Verify bcrypt hashes passwords properly and plain passwords are not recoverable."""
    raw = "MySecretPass2026!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert hashed.startswith("$2b$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_user_registration_and_login(client, db_session):
    """Verify registration creates hashed password and login issues JWT (S2, S3)."""
    # Register
    reg_res = client.post(
        "/auth/register",
        json={"name": "Alice Green", "email": "alice@nexusai.com", "password": "SecurePassword123!"}
    )
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "token" in reg_data
    assert reg_data["user"]["email"] == "alice@nexusai.com"

    # Verify password in database is NOT plaintext
    db_user = db_session.query(User).filter(User.email == "alice@nexusai.com").first()
    assert db_user is not None
    assert db_user.password != "SecurePassword123!"
    assert verify_password("SecurePassword123!", db_user.password) is True

    # Login
    login_res = client.post(
        "/auth/login",
        json={"email": "alice@nexusai.com", "password": "SecurePassword123!"}
    )
    assert login_res.status_code == 200
    assert "token" in login_res.json()

    # Invalid login fails
    bad_login = client.post(
        "/auth/login",
        json={"email": "alice@nexusai.com", "password": "WrongPassword"}
    )
    assert bad_login.status_code == 401


def test_protected_routes_require_jwt(client):
    """Verify unauthenticated access to datasets and chat is rejected with 401 (S2)."""
    assert client.get("/datasets/").status_code == 401
    assert client.post("/ai/chat", json={"message": "Total revenue"}).status_code == 401
    assert client.get("/ai/predict/sales/model-info").status_code == 401


def test_sql_injection_defense_users_table(db_session):
    """Verify queries attempting to read from 'users' table are strictly blocked (S4 fix)."""
    safe, msg = is_safe_sql("SELECT email, password FROM users")
    assert safe is False
    assert "not permitted" in msg or "Access denied" in msg


def test_sql_injection_defense_system_functions(db_session):
    """Verify queries attempting pg_sleep or system probes are strictly blocked (S4 fix)."""
    safe1, msg1 = is_safe_sql("SELECT pg_sleep(30) FROM finance_records")
    assert safe1 is False
    assert "Forbidden system function" in msg1

    safe2, msg2 = is_safe_sql("SELECT version() FROM finance_records")
    assert safe2 is False

    safe3, msg3 = is_safe_sql("SELECT * FROM finance_records; DROP TABLE users;")
    assert safe3 is False


def test_safe_chat_query_execution(db_session, seeded_dataset):
    """Verify authorized financial queries execute safely and return engine identifier."""
    result = process_chat_query(db=db_session, question="What is the total revenue?", dataset_id=seeded_dataset.id)
    assert "revenue" in result["answer"].lower()
    assert result["engine"] == "rule_engine"
    assert "sql" in result
    assert "finance_records" in result["sql"]
