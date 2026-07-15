import os
from typing import Any

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def fetch_json(path: str, *, timeout: int = 10) -> Any:
    """Call a FastAPI endpoint and return JSON data."""
    response = requests.get(f"{API_BASE_URL}{path}", timeout=timeout)
    response.raise_for_status()
    return response.json()


def post_json(path: str, payload: dict[str, Any], *, timeout: int = 60) -> Any:
    """POST JSON payload to a FastAPI endpoint."""
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()
