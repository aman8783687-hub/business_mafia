"""Loads secrets from a repo-root .env (gitignored, local/dev convenience)
without overriding real environment variables (GitHub Actions secrets).
Never commit .env; it exists so a local run doesn't need every secret
exported by hand."""
from __future__ import annotations

import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_PATH.exists():
        return values
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get(name: str, default: str | None = None) -> str:
    # Real env wins over .env. GitHub secrets pasted with a trailing
    # newline break URLs and tokens, so always strip.
    if name in os.environ:
        return os.environ[name].strip()
    env = load_env()
    if name in env:
        return env[name].strip()
    if default is not None:
        return default
    raise RuntimeError(f"{name} is not set in the environment or {ENV_PATH}")


def export_to_environ() -> None:
    for key, value in load_env().items():
        os.environ.setdefault(key, value)
