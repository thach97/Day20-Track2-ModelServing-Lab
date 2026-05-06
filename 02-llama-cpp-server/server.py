#!/usr/bin/env python3
"""Custom llama.cpp Python server wrapper with /metrics support.

This wraps llama_cpp.server.create_app and adds a Prometheus-style metrics
endpoint so the lab's smoke tests and record-metrics script work.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any

import anyio
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

from llama_cpp.server.app import create_app
from llama_cpp.server.cli import add_args_from_model, parse_model_from_args
from llama_cpp.server.settings import ModelSettings, ServerSettings, Settings

METRICS = {
    "llamacpp:tokens_predicted_total": 0.0,
    "llamacpp:prompt_tokens_total": 0.0,
    "llamacpp:n_decode_total": 0.0,
    "llamacpp:kv_cache_usage_ratio": 0.0,
    "llamacpp:requests_processing": 0.0,
    "llamacpp:requests_deferred": 0.0,
}
_METRICS_LOCK = anyio.Lock()


def record_metrics(usage: dict[str, Any]) -> None:
    """Update counters from the OpenAI-style usage object."""
    if not usage:
        return
    prompt_tokens = float(usage.get("prompt_tokens", 0))
    completion_tokens = float(usage.get("completion_tokens", 0))
    total_tokens = float(usage.get("total_tokens", 0))
    METRICS["llamacpp:prompt_tokens_total"] += prompt_tokens
    METRICS["llamacpp:tokens_predicted_total"] += completion_tokens
    METRICS["llamacpp:n_decode_total"] += total_tokens


def build_app(server_settings: ServerSettings, model_settings: list[ModelSettings]) -> FastAPI:
    app = create_app(server_settings=server_settings, model_settings=model_settings)

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        async with _METRICS_LOCK:
            METRICS["llamacpp:requests_processing"] += 1.0
        try:
            response = await call_next(request)
            if request.method == "POST" and request.url.path in (
                "/v1/chat/completions",
                "/v1/completions",
            ):
                text = None
                try:
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    ):
                        body_bytes = await response.body()
                        text = body_bytes.decode("utf-8")
                        payload = json.loads(text)
                        record_metrics(payload.get("usage", {}))
                except Exception:
                    pass
            return response
        finally:
            async with _METRICS_LOCK:
                METRICS["llamacpp:requests_processing"] = max(
                    0.0, METRICS["llamacpp:requests_processing"] - 1.0
                )

    @app.get("/metrics")
    async def metrics_endpoint() -> PlainTextResponse:
        lines = []
        async with _METRICS_LOCK:
            for name, value in METRICS.items():
                lines.append(f"{name} {value}")
        return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain")

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="llama-cpp-python server wrapper")
    add_args_from_model(parser, Settings)
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of Uvicorn workers",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = parse_model_from_args(Settings, args)
    server_settings = parse_model_from_args(ServerSettings, args)
    model_settings = [parse_model_from_args(ModelSettings, args)]

    app = build_app(server_settings=server_settings, model_settings=model_settings)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
