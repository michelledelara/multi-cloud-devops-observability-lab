"""HTTP service with bounded metrics, structured logs and opt-in fault injection."""
import json
import logging
import math
import os
import time
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from flask import Flask, Response, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram,
    ProcessCollector, PlatformCollector, GCCollector, generate_latest,
)


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        APP_ENV=os.getenv("APP_ENV", "local"),
        ENABLE_FAULTS=os.getenv("ENABLE_FAULTS", "false").lower() == "true",
        LOG_DIR=os.getenv("LOG_DIR", ""),
    )
    app.config.update(config or {})
    registry = CollectorRegistry()
    ProcessCollector(registry=registry)
    PlatformCollector(registry=registry)
    GCCollector(registry=registry)
    requests = Counter("lab_http_requests_total", "Completed HTTP requests",
                       ["method", "route", "status"], registry=registry)
    duration = Histogram("lab_http_request_duration_seconds", "Request latency",
                         ["method", "route"],
                         buckets=(.005, .01, .025, .05, .1, .25, .5, 1, 2, 5),
                         registry=registry)
    inflight = Gauge("lab_http_requests_in_progress", "Active business requests",
                     registry=registry)
    app.extensions["metrics_registry"] = registry
    logger = logging.getLogger(f"lab.{uuid.uuid4().hex}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(logging.StreamHandler())
    if app.config["LOG_DIR"]:
        os.makedirs(app.config["LOG_DIR"], exist_ok=True)
        logger.addHandler(RotatingFileHandler(
            os.path.join(app.config["LOG_DIR"], "app.jsonl"),
            maxBytes=5_000_000, backupCount=3, encoding="utf-8"))
    app.extensions["structured_logger"] = logger
    excluded = {"/metrics", "/healthz", "/readyz"}

    @app.before_request
    def begin():
        g.started = time.perf_counter()
        g.request_id = str(uuid.uuid4())
        g.observed = request.path not in excluded
        if g.observed:
            inflight.inc()

    @app.after_request
    def observe(response):
        response.headers["X-Request-ID"] = g.request_id
        if g.observed:
            elapsed = time.perf_counter() - g.started
            # Templates bound label cardinality; never use raw URLs or user IDs.
            route = request.url_rule.rule if request.url_rule else "unmatched"
            method = request.method if request.method in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} else "OTHER"
            requests.labels(method, route, str(response.status_code)).inc()
            duration.labels(method, route).observe(elapsed)
            inflight.dec()
            logger.info(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "ERROR" if response.status_code >= 500 else "INFO",
                "service": "lab-api", "environment": app.config["APP_ENV"],
                "method": method, "route": route, "status": response.status_code,
                "duration_ms": round(elapsed * 1000, 3), "request_id": g.request_id,
            }))
        return response

    @app.get("/")
    def index():
        return jsonify(service="lab-api", project="multi-cloud-devops-observability-lab",
                       environment=app.config["APP_ENV"], version="1.0.0")

    @app.get("/healthz")
    def health():
        return jsonify(status="healthy")

    @app.get("/readyz")
    def ready():
        # No downstream dependencies in this reference service.
        return jsonify(status="ready")

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(registry), content_type=CONTENT_TYPE_LATEST)

    @app.get("/work")
    def work():
        try:
            delay = float(request.args.get("delay_ms", "0"))
        except ValueError:
            return jsonify(error="delay_ms must be a finite number from 0 to 2000"), 400
        if not math.isfinite(delay) or not 0 <= delay <= 2000:
            return jsonify(error="delay_ms must be a finite number from 0 to 2000"), 400
        time.sleep(delay / 1000)
        return jsonify(result="completed", delay_ms=delay)

    @app.get("/fail")
    def fail():
        if not app.config["ENABLE_FAULTS"]:
            return jsonify(error="fault injection is disabled"), 403
        return jsonify(error="controlled failure", request_id=g.request_id), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
