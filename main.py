import os

from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI(
    title="Lab 2 REST API",
    description="Базовий REST-сервіс для лабораторної роботи з Git. p.s оновлено для коміта",
    version="1.0.0"
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/testdb")

# Налаштування SQLAlchemy
engine = create_engine(DATABASE_URL)

@app.get("/db-test")
def test_db_connection():
    try:
        # Спроба підключитися до БД і виконати простий запит
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1;"))
            return {"status": "success", "message": "Підключення до бази даних успішне!", "result": [row[0] for row in result]}
    except SQLAlchemyError as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
def read_root():
    return {"message": "Hello, Git!"}

@app.get("/ping")
def ping():
    return {"ping": "pong"}

# Ендпоінт для перевірки статусу

@app.get("/status")
def get_status():
    return {"status": "ok"}