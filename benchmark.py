#!/usr/bin/env python3

import os
import sys

from typing import List, NamedTuple
from json import loads as parse_json, dump as print_json
from time import monotonic_ns

from json_logic import jsonLogic
from json_logic.extras import EXTRAS

def usage() -> None:
    print("%s <repeat-count> <logic> <data>\n" % (sys.argv[0] if sys.argv else "benchmark.py"))

class Stats(NamedTuple):
    min: int
    max: int
    sum: int
    avg: float
    median: float

def stats(times: List[int]) -> Stats:
    times.sort()

    count = len(times)
    if count % 2 == 0:
        median = (times[count // 2 - 1] + times[count // 2]) / 2
    else:
        median = times[count // 2]

    sum_time = sum(times)

    return Stats(
        min = min(times),
        max = max(times),
        sum = sum_time,
        avg = sum_time / count,
        median = median,
    )

def print_stats(times: List[int], name: str) -> None:
    st = stats(times)

    print("%-5s %10.3f %10.3f %10.3f %10.3f %10.3f" % (
        name,
        st.min    / 1_000_000,
        st.max    / 1_000_000,
        st.avg    / 1_000_000,
        st.median / 1_000_000,
        st.sum    / 1_000_000,
    ))

def main() -> None:
    if len(sys.argv) != 4:
        usage()
        sys.exit(1)

    count = int(sys.argv[1], 10)
    logic_str = sys.argv[2]
    data_str  = sys.argv[3]

    # to test if its all valid:
    logic = parse_json(logic_str)
    data  = parse_json(data_str)
    jsonLogic(logic, data, EXTRAS)

    parse_times: List[int] = []
    apply_times: List[int] = []
    print_times: List[int] = []
    sum_times:   List[int] = []

    with open(os.devnull, 'w') as devnull:
        for _ in range(count):
            start = monotonic_ns()

            logic = parse_json(logic_str)
            data  = parse_json(data_str)

            parse_done = monotonic_ns()

            result = jsonLogic(logic, data, EXTRAS)

            apply_done = monotonic_ns()

            print_json(result, devnull)
            devnull.write('\n') # just to be really fair

            print_done = monotonic_ns()

            parse_times.append(parse_done - start)
            apply_times.append(apply_done - parse_done)
            print_times.append(print_done - apply_done)
            sum_times.append(print_done - start)

    print("             min        max        avg     median        sum")
    print_stats(parse_times, "parse")
    print_stats(apply_times, "apply")
    print_stats(print_times, "print")
    print_stats(sum_times,   "sum")

if __name__ == '__main__':
    main()
