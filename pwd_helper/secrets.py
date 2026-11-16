"""Unified Secrets Resolver.

Provides safe resolution of sensitive credentials (e.g. Telegram tokens, cloud
API keys) across:
1. System Environment Variables (e.g., TELEGRAM_BOT_TOKEN)
2. Local ignored secrets file (.secrets.json)
3. Local ignored environment file (.env)
4. Provided runtime config dictionary (fallback / legacy)

This prevents accidental exposure of authentication tokens in git repositories.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SECRETS_FILE = _REPO_ROOT / ".secrets.json"
_ENV_FILE = _REPO_ROOT / ".env"


def _read_env_file(path: Path) -> dict[str, str]:
    """Parse a simple key=value .env file without external dependencies."""
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k:
                    result[k] = v
    except Exception:
        pass
    return result


def set_secret(key: str, value: str, path: Path | None = None) -> None:
    """Store a secret in the ignored .env file, replacing only its own entry."""
    if not key or "=" in key or "\n" in key:
        raise ValueError("Invalid environment variable name")

    env_path = path or _ENV_FILE
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    replacement = f'{key}="{str(value).replace(chr(34), chr(92) + chr(34))}"'
    output: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            line_key = stripped.split("=", 1)[0].strip()
            if line_key == key:
                if not replaced:
                    output.append(replacement)
                    replaced = True
                continue
        output.append(line)
    if not replaced:
        if output and output[-1].strip():
            output.append("")
        output.append(replacement)

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    try:
        env_path.chmod(0o600)
    except OSError:
        pass


def _read_secrets_json(path: Path) -> dict[str, Any]:
    """Parse local JSON secrets file."""
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_secret(
    key: str,
    config: Mapping[str, Any] | None = None,
    default: str = "",
    env_name: str | None = None,
) -> str:
    """Resolve a secret token or key safely.

    Lookup precedence:
    1. Direct environment variable (env_name or key.upper())
    2. Local .secrets.json (exact key or lower/upper)
    3. Local .env file
    4. config dictionary (if key value is 'env:VAR', resolves VAR from env)
    5. default
    """
    primary_env = env_name or key.upper()
    if os.getenv(primary_env):
        return os.environ[primary_env].strip()

    # If config explicitly specifies an env pointer (e.g. "env:TELEGRAM_BOT_TOKEN")
    if config and isinstance(config, Mapping):
        val = str(config.get(key, "")).strip()
        if val.startswith("env:"):
            target_var = val.split(":", 1)[1].strip()
            if os.getenv(target_var):
                return os.environ[target_var].strip()

    # Check local .secrets.json
    sec = _read_secrets_json(_SECRETS_FILE)
    if key in sec and str(sec[key]).strip():
        return str(sec[key]).strip()
    if key.lower() in sec and str(sec[key.lower()]).strip():
        return str(sec[key.lower()]).strip()
    if primary_env in sec and str(sec[primary_env]).strip():
        return str(sec[primary_env]).strip()

    # Check local .env
    env_dict = _read_env_file(_ENV_FILE)
    if primary_env in env_dict and env_dict[primary_env].strip():
        return env_dict[primary_env].strip()
    if key in env_dict and env_dict[key].strip():
        return env_dict[key].strip()

    # Fallback to direct config value if provided and not a placeholder/env: pointer
    if config and isinstance(config, Mapping):
        raw_val = str(config.get(key, "")).strip()
        if raw_val and not raw_val.startswith("env:"):
            return raw_val

    return default
