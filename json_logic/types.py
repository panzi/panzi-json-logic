from __future__ import annotations

from typing import Union, Callable
from datetime import date, datetime

__all__ = 'JsonValue',

type JsonValue = Union[int, float, bool, str, date, datetime, None, list['JsonValue'], dict[str, 'JsonValue']] # type: ignore

type Operation = Callable[..., JsonValue]
type Operations = dict[str, Union[Operation, 'Operations']]
