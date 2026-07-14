import json
from typing import Any


def to_json(value: Any) -> str:
    return json.dumps(value)


def from_json(value: str) -> Any:
    return json.loads(value)
