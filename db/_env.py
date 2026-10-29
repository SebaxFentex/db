from __future__ import annotations

import os
from typing import Callable, TypeVar


class MissingEnvironmentVariableError(RuntimeError):
    """Raised when a required environment variable is missing."""


T = TypeVar("T")


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise MissingEnvironmentVariableError(
            f"La variable de entorno '{name}' es requerida y no esta definida."
        )
    return value


def get_typed_env(name: str, caster: Callable[[str], T], default: T | None = None) -> T | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return caster(value)
    except Exception as exc:  # pragma: no cover
        raise ValueError(
            f"La variable de entorno '{name}' no tiene un valor valido: {value!r}"
        ) from exc
