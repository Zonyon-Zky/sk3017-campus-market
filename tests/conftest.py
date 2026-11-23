
import base64
import os
from pathlib import Path

import pymysql
import pytest

from app import create_app

ROOT = Path(__file__).resolve().parent.parent
TEST_DB = os.getenv("TEST_DB_NAME", "campus_market_test")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
}
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZfZkAAAAASUVORK5CYII="
)


def execute_script(path, database):
    connection = pymysql.connect(**DB_CONFIG, database=database, charset="utf8mb4", autocommit=True)
    sql = path.read_text(encoding="utf-8").replace("campus_market", database)
    with connection.cursor() as cursor:
        for statement in sql.split(";"):
            if statement.strip():
                cursor.execute(statement)
    connection.close()


def reset_database():
    server = pymysql.connect(**DB_CONFIG, charset="utf8mb4", autocommit=True)
    with server.cursor() as cursor:
        cursor.execute(f"DROP DATABASE IF EXISTS `{TEST_DB}`")
        cursor.execute(f"CREATE DATABASE `{TEST_DB}` DEFAULT CHARACTER SET utf8mb4")
    server.close()
    execute_script(ROOT / "database/schema.sql", TEST_DB)
    execute_script(ROOT / "database/seed.sql", TEST_DB)


@pytest.fixture(autouse=True)
def database():
    reset_database()


@pytest.fixture()
def app(tmp_path):
    upload = tmp_path / "uploads"
    upload.mkdir()
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DB_HOST": DB_CONFIG["host"],
        "DB_PORT": DB_CONFIG["port"],
        "DB_USER": DB_CONFIG["user"],
        "DB_PASSWORD": DB_CONFIG["password"],
        "DB_NAME": TEST_DB,
        "UPLOAD_FOLDER": str(upload),
    })


@pytest.fixture()
def client(app):
    return app.test_client()


def db_connection():
    return pymysql.connect(**DB_CONFIG, database=TEST_DB, charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)


def login(client, username="demo", password="123456"):
    return client.post("/auth/login", data={"username": username, "password": password}, follow_redirects=True)
