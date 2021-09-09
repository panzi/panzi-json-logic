from __future__ import annotations

from typing import Any, Optional
from datetime import datetime, date, time, timedelta, timezone
from math import isnan

import re

from ..types import Operations
from ..builtins import to_float, to_string, var, in_, less_than, less_than_or_equal, greater_than, greater_than_or_equal

def to_bool(data=None, value: Any=None) -> bool:
    if type(value) is bool:
        return value # type: ignore

    if isinstance(value, float):
        if isnan(value):
            return False
        return bool(value)

    if isinstance(value, (str, int, list, dict, bool)):
        return bool(value)

    # dict, date, datetime
    return True

def not_(data=None, value: Any=None) -> bool:
    if type(value) is bool:
        return not value

    if isinstance(value, float):
        if isnan(value):
            return True
        return value == 0.0

    if isinstance(value, (str, int, list, dict, bool)):
        return not bool(value)

    # dict, date, datetime
    return False

def add(data=None, a=None, b=None, *_ignored) -> float:
    return to_float(a) + to_float(b)

def parse_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return value

    if isinstance(value, date):
        return datetime.combine(value, time(), timezone.utc)

    value = datetime.fromisoformat(to_string(value))

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value

def to_int(value: Any) -> int:
    value = to_float(value)
    if isnan(value):
        return 0
    return int(value)

def plus_time(data=None, dtstr=None, value=None, unit=None, *_ignored) -> datetime:
    dt = parse_time(dtstr)

    if unit == 'year':
        return dt.replace(year=dt.year + to_int(value))

    if unit == 'month':
        month  = dt.month + to_int(value)
        years  = (month - 1) // 12
        year   = dt.year + years
        month -= years * 12

        return dt.replace(year=year, month=month)

    if unit == 'day':
        return dt + timedelta(days=to_float(value))

    if unit == 'hour':
        return dt + timedelta(hours=to_float(value))

    raise ValueError(f'illegal unit: {unit!r}')

OPTIONAL_PREFIX = "URN:UVCI:"
UVCI_SPLIT = re.compile('[/#:]')

def extract_from_uvci(data=None, uvci=None, index=None, *_ignored) -> Optional[str]:
    index = to_int(index)
    if uvci is None or index < 0:
        return None

    uvci = to_string(uvci)
    if uvci.startswith(OPTIONAL_PREFIX):
        uvci = uvci[len(OPTIONAL_PREFIX):]

    fragments = UVCI_SPLIT.split(uvci)
    return fragments[index] if index < len(fragments) else None

BUILTINS: Operations = {
    '===': lambda a=None, b=None, *_ignored: a == b,
    '<':   less_than,
    '>':   greater_than,
    '<=':  less_than_or_equal,
    '>=':  greater_than_or_equal,
    '!':   not_,
    '+':   add,
    'in':  in_,
    'var': var,
    'before':     lambda data=None, a=None, b=None, *_ignored: parse_time(a) <  parse_time(b),
    'not-before': lambda data=None, a=None, b=None, *_ignored: parse_time(a) >= parse_time(b),
    'after':      lambda data=None, a=None, b=None, *_ignored: parse_time(a) >  parse_time(b),
    'not-after':  lambda data=None, a=None, b=None, *_ignored: parse_time(a) <= parse_time(b),
    'plusTime':        plus_time,
    'extractFromUVCI': extract_from_uvci,
}
