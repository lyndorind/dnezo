import logging
import os

from prometheus_client import start_http_server

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider

from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter,
)

from opentelemetry.exporter.prometheus import PrometheusMetricReader

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.logging.handler import LoggingHandler

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.sdk.metrics import MeterProvider

from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor


def configure_telemetry(app, engine):
    logger = logging.getLogger("lab2-rest-api")
    logger.setLevel(logging.INFO)

    # Під час локальних тестів без Docker телеметрія не запускається
    if os.getenv("ENABLE_OTEL", "false").lower() != "true":
        meter = metrics.get_meter("lab2-rest-api")

        return (
            meter.create_counter("app_http_requests"),
            meter.create_histogram(
                "app_http_request_duration",
                unit="s",
            ),
            logger,
        )

    # Загальна інформація про сервіс
    resource = Resource.create({
        "service.name": os.getenv(
            "OTEL_SERVICE_NAME",
            "lab2-rest-api",
        ),
        "service.version": "1.0.0",
    })

    # ---------------- TRACES ----------------

    tracer_provider = TracerProvider(resource=resource)

    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter())
    )

    trace.set_tracer_provider(tracer_provider)

    # Інструментування FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Інструментування SQLAlchemy
    SQLAlchemyInstrumentor().instrument(engine=engine)

    # ---------------- METRICS ----------------

    start_http_server(
        port=9464,
        addr="0.0.0.0",
    )

    metric_reader = PrometheusMetricReader()

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )

    metrics.set_meter_provider(meter_provider)

    meter = metrics.get_meter("lab2-rest-api")

    request_counter = meter.create_counter(
        "app_http_requests",
        description="Total number of HTTP requests",
        unit="{request}",
    )

    request_duration = meter.create_histogram(
        "app_http_request_duration",
        description="HTTP request duration",
        unit="s",
    )

    # ---------------- LOGS ----------------

    logger_provider = LoggerProvider(
        resource=resource,
    )

    log_exporter = OTLPLogExporter()

    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(log_exporter)
    )

    set_logger_provider(logger_provider)

    logging_handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=logger_provider,
    )

    logger.addHandler(logging_handler)

    logger.info("OpenTelemetry initialized successfully")

    return request_counter, request_duration, logger