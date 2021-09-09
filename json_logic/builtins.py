from __future__ import annotations

from typing import Any, List, Iterable
from datetime import date, datetime, time
from time import mktime
from wsgiref.handlers import format_date_time
from math import isnan

import json

from .types import JsonValue, Operations

NAN = float('nan')
NUMERIC = (int, float)
EPOCH = datetime.utcfromtimestamp(0)

def equals(data=None, a=None, b=None, *_ignored) -> bool:
    atype = type(a)
    if atype is type(b):
        if atype in (list, dict):
            return a is b
        return a == b

    if isinstance(a, NUMERIC):
        if isinstance(b, NUMERIC):
            return a == b
        return a == to_float(b)

    if isinstance(b, NUMERIC):
        return to_float(a) == b

    if a is None or b is None:
        return False

    if isinstance(a, str):
        if isinstance(b, bool):
            return to_float(a) == to_float(b)

        if isinstance(b, (list, dict)):
            return a == to_string(b)

        raise TypeError

    if isinstance(a, bool):
        return to_float(a) == to_float(b)

    if isinstance(a, (list, dict)):
        if isinstance(b, (list, dict)):
            return False

        if isinstance(b, str):
            return to_string(a) == b

        if isinstance(b, bool):
            return to_float(a) == to_float(b)

        raise TypeError

    raise TypeError

def to_float(a: Any) -> float:
    if a is None:
        return 0.0

    if isinstance(a, list):
        if not a:
            return 0.0
        elif len(a) > 1:
            return NAN
        else:
            return to_float(a[0])

    if isinstance(a, dict):
        return NAN

    if isinstance(a, str) and a.strip().lower() in ('inf', '-inf', '+inf'):
        # Python's float() would allow these, but JavaScript won't recognize these
        return NAN

    if isinstance(a, datetime):
        return (a - EPOCH).total_seconds() * 1000.0

    if isinstance(a, date):
        return (datetime.combine(a, time()) - EPOCH).total_seconds() * 1000.0

    try:
        return float(a)
    except ValueError:
        return NAN

def to_string(value: Any) -> str:
    if isinstance(value, str):
        return value

    if isinstance(value, NUMERIC):
        return str(value)

    if value is None:
        return 'null'

    if value is True:
        return 'true'

    if value is False:
        return 'false'

    if isinstance(value, list):
        return ','.join(to_string(item) for item in value)

    if isinstance(value, dict):
        return '[object Object]'

    if isinstance(value, (date, datetime)):
        return format_date_time(mktime(value.timetuple()))

    return str(value)

def to_bool(data=None, value: Any=None) -> bool:
    if type(value) is bool:
        return value # type: ignore

    if isinstance(value, float):
        if isnan(value):
            return False
        return bool(value)

    if isinstance(value, (str, int, list, bool)):
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

    if isinstance(value, (str, int, list, bool)):
        return not bool(value)

    # dict, date, datetime
    return False

def add(data=None, *args: Any) -> float:
    value = 0.0
    for arg in args:
        value += to_float(arg)
    return value

def mul(data=None, *args: Any) -> float:
    value = 1.0
    for arg in args:
        value *= to_float(arg)
    return value

def json_default(arg: Any) -> JsonValue:
    if isinstance(arg, (date, datetime)):
        return arg.isoformat()

    argtype = type(arg)
    raise TypeError(f'unhandled type: {argtype.__module__}.{argtype.__name__}')

def log(data=None, arg: Any=None, *_ignored) -> Any:
    print(json.dumps(arg, default=json_default))
    return arg

def less_than(data=None, a=None, b=None, *_ignored) -> bool:
    if isinstance(a, NUMERIC):
        return a < to_float(b)

    if isinstance(b, NUMERIC):
        return to_float(a) < b

    if isinstance(a, str):
        return a < to_string(b)

    if isinstance(b, str):
        return to_string(a) < b

    return to_float(a) < to_float(b)

def greater_than(data=None, a=None, b=None, *_ignored) -> bool:
    if isinstance(a, NUMERIC):
        return a > to_float(b)

    if isinstance(b, NUMERIC):
        return to_float(a) > b

    if isinstance(a, str):
        return a > to_string(b)

    if isinstance(b, str):
        return to_string(a) > b

    return to_float(a) > to_float(b)

def less_than_or_equal(data=None, a=None, b=None, *_ignored) -> bool:
    if isinstance(a, NUMERIC):
        return a <= to_float(b)

    if isinstance(b, NUMERIC):
        return to_float(a) <= b

    if isinstance(a, str):
        return a <= to_string(b)

    if isinstance(b, str):
        return to_string(a) <= b

    return to_float(a) <= to_float(b)

def greater_than_or_equal(data=None, a=None, b=None, *_ignored) -> bool:
    if isinstance(a, NUMERIC):
        return a >= to_float(b)

    if isinstance(b, NUMERIC):
        return to_float(a) >= b

    if isinstance(a, str):
        return a >= to_string(b)

    if isinstance(b, str):
        return to_string(a) >= b

    return to_float(a) >= to_float(b)

def substr(data=None, string=None, index=None, length=None, *_ignored) -> str:
    string = to_string(string)
    index  = to_float(index)

    strlen = len(string)
    if isnan(index):
        index = 0
    elif index < 0:
        index = -index
        if index >= strlen:
            index = 0
        else:
            index = strlen - int(index)
    else:
        index = int(index)
        if index >= strlen:
            index = strlen

    if length is None:
        end_index = strlen
    else:
        length = to_float(length)
        if isnan(length):
            end_index = index
        else:
            length = int(length)
            if length < 0:
                end_index = strlen + length
                if end_index < index:
                    end_index = index
            else:
                end_index = index + length

    return string[index:end_index]

def substr_utf16(data=None, string=None, index=None, length=None, *_ignored) -> str:
    string = to_string(string).encode('UTF-16')
    index  = to_float(index)

    strlen = len(string)
    if isnan(index):
        index = 0
    elif index < 0:
        index = -index
        if index >= strlen:
            index = 0
        else:
            index = strlen - int(index)
    else:
        index = int(index)
        if index >= strlen:
            index = strlen

    if length is None:
        end_index = strlen
    else:
        length = to_float(length)
        if isnan(length):
            end_index = index
        else:
            length = int(length)
            if length < 0:
                end_index = strlen + length
                if end_index < index:
                    end_index = index
            else:
                end_index = index + length

    return string[index:end_index].decode('UTF-16', errors='ignore')

def missing(data=None, *args: Any) -> List[str]:
    keys: Iterable[Any]
    if args:
        arg0 = args[0]
        if isinstance(arg0, list):
            keys = arg0
        else:
            keys = args
    else:
        keys = args

    missing_keys: List[str] = []

    for key in keys:
        value = var(data, key)
        if value is None or value == '':
            missing_keys.append(key)

    return missing_keys

def missing_some(data=None, need_count: Any=0, keys: Any=None, *_ignored) -> List[str]:
    if not isinstance(keys, list):
        return []

    need_count = to_float(need_count)
    missing_keys = missing(data, keys)
    if len(keys) - len(missing_keys) >= need_count:
        return []
    
    return missing_keys

def var(data=None, key=None, default=None) -> Any:
    if key is None or key == '':
        return data
    
    props = to_string(key).split('.')
    for prop in props:
        if data is None:
            return default

        data = data.get(prop)

    if data is None:
        return default

    return data

def merge(data=None, *args: Any) -> List[Any]:
    items: List[Any] = []
    for arg in args:
        if isinstance(arg, list):
            items.extend(arg)
        else:
            items.append(arg)
    return items

def in_(a=None, b=None, *_ignored) -> bool:
    return a in b if isinstance(a, list) else False

BUILTINS: Operations = {
    '==':  equals,
    '!=':  lambda a=None, b=None, *_ignored: not equals(a, b),
    '===': lambda a=None, b=None, *_ignored: a == b,
    '!==': lambda a=None, b=None, *_ignored: a != b,
    '<':   less_than,
    '>':   greater_than,
    '<=':  less_than_or_equal,
    '>=':  greater_than_or_equal,
    '!':   not_,
    '!!':  to_bool,
    '+':   add,
    '*':   mul,
    '-':   lambda a=None, b=None, *_ignored: -to_float(a) if b is None else to_float(a) - to_float(b),
    '/':   lambda a=None, b=None, *_ignored: to_float(a) / to_float(b),
    '%':   lambda a=None, b=None, *_ignored: to_float(a) % to_float(b),
    'in':  in_,
    'min': lambda *args: min(to_float(arg) for arg in args) if args else NAN,
    'max': lambda *args: max(to_float(arg) for arg in args) if args else NAN,
    'cat': lambda *args: ','.join(to_string(arg) for arg in args),
    'var': var,
    'substr':       substr,
    'merge':        merge,
    'missing':      missing, # type: ignore
    'missing_some': missing_some,
}
