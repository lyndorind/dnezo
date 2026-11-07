import os
import time

from fastapi import FastAPI, Request

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from telemetry import configure_telemetry


app = FastAPI(
    title="Lab 2 REST API",
    description="REST API with OpenTelemetry monitoring",
    version="1.0.0",
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/testdb",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# Ініціалізація OpenTelemetry
request_counter, request_duration, logger = configure_telemetry(
    app,
    engine,
)


# Middleware для вимірювання HTTP-запитів
@app.middleware("http")
async def collect_http_metrics(request: Request, call_next):
    start_time = time.perf_counter()

    status_code = "500"

    try:
        response = await call_next(request)

        status_code = str(response.status_code)

        return response

    except Exception:
        logger.exception("HTTP request failed")
        raise

    finally:
        duration = time.perf_counter() - start_time

        attributes = {
            "method": request.method,
            "status_code": status_code,
        }

        request_counter.add(1, attributes)

        request_duration.record(
            duration,
            attributes,
        )

        logger.info(
            "HTTP request completed: %s %s status=%s",
            request.method,
            request.url.path,
            status_code,
        )


@app.get("/db-test")
def test_db_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1;"))

            logger.info("Database connection successful")

            return {
                "status": "success",
                "message": "Підключення до бази даних успішне!",
                "result": [row[0] for row in result],
            }

    except SQLAlchemyError:
        logger.exception("Database connection failed")

        return {
            "status": "error",
            "message": "Database connection failed",
        }


@app.get("/")
def read_root():
    logger.info("Root endpoint requested")

    return {
        "message": "Hello, Git!"
    }


@app.get("/ping")
def ping():
    logger.info("Ping endpoint requested")

    return {
        "ping": "pong"
    }


@app.get("/status")
def get_status():
    logger.info("Status endpoint requested")

    return {
        "status": "ok"
    }