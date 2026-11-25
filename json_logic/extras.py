from typing import Any
from datetime import datetime, timezone

from .builtins import BUILTINS, to_number
from .types import Operations, JsonValue
from .cert_logic.builtins import parse_time

def op_time_since(args: list[JsonValue], data: Any) -> float:
    timestamp = args[0] if args else None
    dt = parse_time(timestamp)
    return (datetime.utcnow().replace(tzinfo=timezone.utc) - dt).total_seconds() * 1000

def combinations(*lists: list[JsonValue]) -> list[list[JsonValue]]:
    combinations: list[list[JsonValue]] = []
    list_count = len(lists)
    if list_count > 0:
        stack = [0] * (list_count + 1)
        item: list[JsonValue] = [None] * list_count
        stack_ptr = 0

        while stack_ptr >= 0:
            if stack_ptr == list_count:
                combinations.append(item[:])
                stack_ptr -= 1
            else:
                list  = lists[stack_ptr]
                index = stack[stack_ptr]

                if index == len(list):
                    stack_ptr -= 1
                else:
                    item[stack_ptr]  = list[index]
                    stack[stack_ptr] = index + 1
                    stack_ptr += 1
                    stack[stack_ptr] = 0

    return combinations

EXTRAS_ONLY: Operations = {
    'now':        lambda args, data: datetime.utcnow().replace(tzinfo=timezone.utc),
    'hours':      lambda args, data: to_number(args[0]) * 60 * 60 * 1000 if args else 0,
    'days':       lambda args, data: to_number(args[0]) * 24 * 60 * 60 * 1000 if args else 0,
    'parseTime':  lambda args, data: parse_time(args[0]) if args else None,
    'formatTime': lambda args, data: parse_time(args[0]).isoformat() if args else None,
    'timeSince':  op_time_since,
    'combinations': lambda args, data: combinations(*args), # type: ignore
    'zip': lambda args, data: [list(item) for item in zip(*args)],
}

EXTRAS: Operations = {
    **BUILTINS,
    **EXTRAS_ONLY,
}
