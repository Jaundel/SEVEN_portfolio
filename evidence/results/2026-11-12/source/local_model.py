# ============================================================
#  File: local_model.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Interface for invoking the local Lemonade Server model.
#  Author(s): Team SEVEN
#  Date: 2025-11-07
# ============================================================
"""Local Lemonade Server adapter for SEVEN's energy-aware router.

Usage (for router integration):
    from local_model import ask_local, LocalModelResponse, LemonadeClientError

    try:
        response = ask_local("What is the capital of France?")
        print(f"Answer: {response.text}")
        print(f"Latency: {response.latency_s:.2f}s")
        print(f"Tokens: {response.tokens_used}")
    except LemonadeClientError as e:
        print(f"Local model failed: {e}")

Environment Variables (all optional):
    LEMONADE_BASE_URL: Base URL for Lemonade Server (default: http://localhost:8000/api/v1)
    LEMONADE_MODEL: Model name to use (default: Llama-3.2-1B-Instruct-Hybrid)
    LEMONADE_RECIPE: Recipe for hybrid routing, e.g., "oga-hybrid" (default: None)
    LEMONADE_DEVICE: Device selector: "cpu", "gpu", "hybrid" (default: None)
    LEMONADE_TIMEOUT_SECONDS: HTTP timeout in seconds (default: 30.0)
    LEMONADE_MAX_RETRIES: Max retry attempts for failed requests (default: 2)
    LEMONADE_BACKOFF_SECONDS: Initial retry backoff interval (default: 0.5)
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional
from urllib.parse import urljoin

import requests

if TYPE_CHECKING:  # pragma: no cover - typing only
    try:
        from .energy import EnergyEstimate
    except ImportError:  # Local execution without package context
        from energy import EnergyEstimate

LOGGER = logging.getLogger(__name__)
DEFAULT_BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_MODEL = "Llama-3.2-1B-Instruct-Hybrid"
DEFAULT_RECIPE = ""
DEFAULT_DEVICE = ""
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF = 0.5


class Spinner:
    """Simple terminal spinner for showing progress."""

    def __init__(self, message: str = "Processing"):
        self.message = message
        self.spinner_chars = "|/-\\"
        self.running = False
        self.thread = None

    def _spin(self):
        """Run the spinner animation."""
        idx = 0
        while self.running:
            char = self.spinner_chars[idx % len(self.spinner_chars)]
            sys.stdout.write(f"\r{self.message}... {char}")
            sys.stdout.flush()
            time.sleep(0.1)
            idx += 1

    def start(self):
        """Start the spinner in a background thread."""
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the spinner and clear the line."""
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * (len(self.message) + 6) + "\r")
        sys.stdout.flush()


class LemonadeClientError(RuntimeError):
    """Raised when a Lemonade Server call fails."""


@dataclass
class LocalModelResponse:
    """Normalized response returned to the router layer.

    Fields:
        prompt: The original user prompt sent to the model
        text: Generated text response from the model
        model: Actual model identifier used (e.g., "amd/Phi-3.5-mini-instruct-onnx-ryzenai-npu")
        latency_s: Total round-trip latency in seconds
        tokens_used: Total tokens consumed (prompt + completion), or None if unavailable
        raw: Full raw JSON response from Lemonade Server for advanced debugging
    """

    prompt: str
    text: str
    model: str
    latency_s: float
    tokens_used: Optional[int]
    raw: Dict[str, Any]
    energy: Optional["EnergyEstimate"] = None
    baseline_energy: Optional["EnergyEstimate"] = None
    energy_savings_wh: Optional[float] = None
    energy_savings_kwh: Optional[float] = None


def _base_url() -> str:
    """Return the Lemonade Server base URL from the environment.

    Returns:
        str: Base URL with trailing slash removed.

    Raises:
        None.

    TODO:
        * Allow per-branch overrides via YAML when multiple servers run locally.
    """
    return os.getenv("LEMONADE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _model_name() -> str:
    """Return the model name or fall back to the default hybrid model."""
    return os.getenv("LEMONADE_MODEL", DEFAULT_MODEL)


def _recipe() -> Optional[str]:
    """Return the Lemonade recipe (e.g., oga-hybrid) for hybrid routing."""
    value = os.getenv("LEMONADE_RECIPE", DEFAULT_RECIPE).strip()
    return value or None


def _device() -> Optional[str]:
    """Return the target device selector (cpu/gpu/hybrid)."""
    value = os.getenv("LEMONADE_DEVICE", DEFAULT_DEVICE).strip()
    return value or None


def _timeout() -> float:
    """Return the HTTP timeout in seconds."""
    raw_timeout = os.getenv("LEMONADE_TIMEOUT_SECONDS")
    return float(raw_timeout) if raw_timeout else DEFAULT_TIMEOUT


def _max_retries() -> int:
    """Return the maximum number of retry attempts for Lemonade calls."""
    raw_value = os.getenv("LEMONADE_MAX_RETRIES")
    try:
        return int(raw_value) if raw_value is not None else DEFAULT_MAX_RETRIES
    except ValueError as exc:
        raise LemonadeClientError("LEMONADE_MAX_RETRIES must be an integer.") from exc


def _backoff_seconds() -> float:
    """Return the initial backoff interval between retries."""
    raw_value = os.getenv("LEMONADE_BACKOFF_SECONDS")
    try:
        return float(raw_value) if raw_value is not None else DEFAULT_BACKOFF
    except ValueError as exc:
        raise LemonadeClientError("LEMONADE_BACKOFF_SECONDS must be a float.") from exc


def _parse_response(data: Dict[str, Any], *, prompt: str, latency: float) -> LocalModelResponse:
    """Validate and normalize the Lemonade response payload.

    Args:
        data: Parsed JSON payload from Lemonade Server.
        prompt: Original user prompt text.
        latency: Total round-trip time in seconds.

    Returns:
        LocalModelResponse: Structured response ready for the router.

    Raises:
        LemonadeClientError: If required fields are missing from the payload.
    """
    choices = data.get("choices")
    if not choices:
        raise LemonadeClientError("Lemonade response missing 'choices'.")

    message = choices[0].get("message")
    if not message or "content" not in message:
        raise LemonadeClientError("Lemonade response missing message content.")

    text = message["content"]
    if text is None:
        raise LemonadeClientError("Lemonade response contained null content.")

    usage = data.get("usage") or {}
    total_tokens = usage.get("total_tokens")
    if total_tokens is not None:
        try:
            total_tokens = int(total_tokens)
        except (TypeError, ValueError) as exc:
            raise LemonadeClientError("Invalid token count in Lemonade response.") from exc

    return LocalModelResponse(
        prompt=prompt,
        text=text.strip(),
        model=data.get("model") or _model_name(),
        latency_s=latency,
        tokens_used=total_tokens,
        raw=data,
    )


def _should_retry(status_code: int) -> bool:
    """Determine whether the HTTP response merits a retry."""
    return 500 <= status_code < 600


def ask_local(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 512,  # Increased from 128 - prompts control brevity, not truncation
    stream: bool = False,
    recipe: Optional[str] = None,
    device: Optional[str] = None,
    timeout: Optional[float] = None,
) -> LocalModelResponse:
    """Send prompts to the local Lemonade Server model.

    Args:
        prompt: Primary user prompt to execute locally.
        system_prompt: Optional instruction layer injected before the user text.
        temperature: Sampling temperature used for chat completions.
        max_tokens: Maximum number of tokens to generate in the completion.
        stream: Whether to request SSE streaming (currently unused).
        recipe: Lemonade recipe identifier (e.g., "oga-hybrid") for hybrid routing.
        device: Explicit device selector ("cpu", "gpu", "hybrid") if supported.
        timeout: Optional per-call timeout override in seconds.

    Returns:
        LocalModelResponse: Normalized text, token usage, and latency data.

    Raises:
        ValueError: If the prompt is empty.
        LemonadeClientError: When the Lemonade request fails or the payload is invalid.

    TODO:
        * Implement streaming mode using Lemonade's SSE endpoint when router supports it.
        * Attach energy metadata (NPU vs GPU) once /system-info is integrated.
        * Surface recipe/device defaults inside the README for ops clarity.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string.")

    spinner = Spinner("Processing Locally")
    spinner.start()
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt.strip()})

        payload: Dict[str, Any] = {
            "model": _model_name(),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        applied_recipe = recipe if recipe else _recipe()
        applied_device = device if device else _device()
        if applied_recipe:
            payload["recipe"] = applied_recipe
        if applied_device:
            payload["device"] = applied_device

        url = urljoin(f"{_base_url()}/", "chat/completions")
        call_timeout = timeout or _timeout()
        backoff = _backoff_seconds()

        attempt = 0
        max_attempts = _max_retries()
        while attempt <= max_attempts:
            start = time.perf_counter()
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=call_timeout,
                    headers={"Content-Type": "application/json"},
                )
            except requests.RequestException as exc:
                if attempt >= max_attempts:
                    raise LemonadeClientError(f"Lemonade request failed: {exc}") from exc
                LOGGER.warning("Lemonade call failed (%s). Retrying in %.2fs.", exc, backoff)
                time.sleep(backoff)
                backoff *= 2
                attempt += 1
                continue

            latency = time.perf_counter() - start

            if response.status_code >= 400:
                should_retry = _should_retry(response.status_code) and attempt < max_attempts
                try:
                    error_payload = response.json()
                except ValueError:
                    error_payload = {"error": {"message": response.text}}

                LOGGER.error("Lemonade error response (%s): %s", response.status_code, error_payload)

                message = error_payload.get("error", {}).get(
                    "message", f"HTTP {response.status_code}"
                )
                if should_retry:
                    LOGGER.warning(
                        "Retryable Lemonade error (%s). Retrying in %.2fs.", message, backoff
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    attempt += 1
                    continue
                raise LemonadeClientError(f"Lemonade Server error: {message}")

            try:
                data = response.json()
            except ValueError as exc:
                raise LemonadeClientError("Failed to parse Lemonade JSON response.") from exc

            result = _parse_response(data, prompt=prompt, latency=latency)
            return result

        raise LemonadeClientError("Exhausted Lemonade retries without a successful call.")
    finally:
        spinner.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if len(sys.argv) < 2:
        print("Usage: python local_model.py \"your prompt here\"")
        sys.exit(1)

    user_prompt = " ".join(sys.argv[1:])

    try:
        demo = ask_local(user_prompt)
        print("=== Lemonade Local Test ===")
        print(f"Model:   {demo.model}")
        print(f"Latency: {demo.latency_s:.2f}s")
        print(f"Tokens:  {demo.tokens_used if demo.tokens_used is not None else 'N/A'}")
        print(f"Output:  {demo.text}")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Lemonade local test failed: {exc}")
