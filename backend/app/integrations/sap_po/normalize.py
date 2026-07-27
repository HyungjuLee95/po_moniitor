from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any


def serialize(value: Any) -> Any:
    try:
        from zeep.helpers import serialize_object

        return serialize_object(value, target_cls=dict)
    except (ImportError, TypeError, ValueError):
        return value


def normalized_key(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def pick(value: Any, *keys: str, default: Any = None) -> Any:
    data = serialize(value)
    if not isinstance(data, dict):
        return default
    lookup = {normalized_key(str(key)): item for key, item in data.items()}
    for key in keys:
        candidate = lookup.get(normalized_key(key))
        if candidate is not None:
            return candidate
    return default


def records(value: Any, record_keys: Iterable[str]) -> list[dict[str, Any]]:
    data = serialize(value)
    expected = {normalized_key(key) for key in record_keys}
    found: list[dict[str, Any]] = []

    def visit(item: Any) -> None:
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if not isinstance(item, dict):
            return
        keys = {normalized_key(str(key)) for key in item}
        if keys & expected:
            found.append(item)
            return
        for child in item.values():
            visit(child)

    visit(data)
    if not found and isinstance(data, dict):
        return [data]
    return found


def iso_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def recursive_values(value: Any, key_name: str) -> list[Any]:
    data = serialize(value)
    expected = normalized_key(key_name)
    result: list[Any] = []

    def visit(item: Any) -> None:
        if isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, dict):
            for key, child in item.items():
                if normalized_key(str(key)) == expected:
                    result.append(child)
                visit(child)

    visit(data)
    return result
