#!/usr/bin/env python3

from typing import Optional, List, Any
from os import listdir
from os.path import dirname, join as joinpath
from io import StringIO

import unittest
import json
import sys
import re

from json_logic import jsonLogic, certLogic
from json_logic.types import JsonValue, Operations
from json_logic.builtins import BUILTINS as JSONLOGIC_BUILTINS, op_substr_utf16
from json_logic.extras import EXTRAS, parse_time
from json_logic.cert_logic.builtins import BUILTINS as CERTLOGIC_BUILTINS

NON_IDENT = re.compile('[^_a-zA-Z0-9]+')
TESTDATA_DIR  = joinpath(dirname(__file__), 'testdata')
CERTLOGIC_DIR = joinpath(TESTDATA_DIR, 'certlogic')

with open(joinpath(TESTDATA_DIR, 'tests.json')) as fp:
    TESTS = json.load(fp)

CERTLOGIC_TESTS: List[dict] = []
for filename in sorted(listdir(CERTLOGIC_DIR)):
    if filename.lower().endswith('.json'):
        with open(joinpath(CERTLOGIC_DIR, filename)) as fp:
            CERTLOGIC_TESTS.append(json.load(fp))

VALID: List[dict]
with open(joinpath(TESTDATA_DIR, 'valid.json')) as fp:
    VALID = json.load(fp)

INVALID: List[dict]
with open(joinpath(TESTDATA_DIR, 'invalid.json')) as fp:
    INVALID = json.load(fp)

RULE: JsonValue
with open(joinpath(TESTDATA_DIR, 'rule.json')) as fp:
    RULE = json.load(fp)

class BasicTests(unittest.TestCase):
    def test_bad_operator(self):
        self.assertRaisesRegex(
            ReferenceError, "Unrecognized operation: 'fubar'",
            jsonLogic, {'fubar': []})

    def test_logging(self):
        arg = [1, 'foo\n', True, None, {}]
        out = StringIO()
        stdout = sys.stdout
        try:
            sys.stdout = out
            result = jsonLogic({'log': [arg]})
        finally:
            sys.stdout = stdout

        self.assertEqual(arg, result)
        self.assertEqual(out.getvalue(), "[1, \"foo\\n\", true, null, {}]\n")

    def test_edge_cases(self):
        self.assertEqual(jsonLogic(None), None, 'Called with null')
        self.assertEqual(jsonLogic({'var': ''}, 0), 0, "Var when data is 'falsy'")
        self.assertEqual(jsonLogic({'var': ''}, None), None, "Var when data is null")
        self.assertEqual(jsonLogic({'var': ['a', 'fallback']}, None), 'fallback', "Fallback works when data is a non-object")

    def test_expanding_functionality(self):
        ops = dict(JSONLOGIC_BUILTINS)

        # Operator is not yet defined
        self.assertRaisesRegex(
            ReferenceError, "Unrecognized operation: 'add_to_a'",
            jsonLogic, {'add_to_a': []}, operations=ops)

        # Set up some outside data, and build a basic function operator
        a = 0
        def add_to_a(data, b=None):
            nonlocal a
            if b is None:
                b = 1
            a += b
            return a

        ops['add_to_a'] = add_to_a
        # New operation executes, returns desired result
        # No args
        self.assertEqual(jsonLogic({'add_to_a': []}, operations=ops), 1)
        # Unary syntactic sugar
        self.assertEqual(jsonLogic({'add_to_a': 41}, operations=ops), 42)
        # New operation had side effects.
        self.assertEqual(a, 42)

        fives: Operations = {
            'add':      lambda data, i: i + 5,
            'subtract': lambda data, i: i - 5,
        }

        ops['fives'] = fives
        self.assertEqual(jsonLogic({'fives.add': 37}, operations=ops), 42)
        self.assertEqual(jsonLogic({'fives.subtract': [47]}, operations=ops), 42)

        # Calling a method with multiple var as arguments.
        ops['times'] = lambda data, a, b: a * b
        self.assertEqual(
            jsonLogic(
                {"times": [{"var": "a"}, {"var": "b"}]},
                {'a': 6, 'b': 7},
                ops
            ),
            42
        )

        # Remove operation:
        del ops['times']

        self.assertRaisesRegex(
            ReferenceError, "Unrecognized operation: 'times'",
            jsonLogic, {'times': [2, 2]}, operations=ops)

        # Calling a method that takes an array, but the inside of the array has rules, too
        ops['array_times'] = lambda data, a: a[0] * a[1]
        self.assertEqual(
            jsonLogic(
                {"array_times": [[{"var": "a"}, {"var": "b"}]]},
                {'a': 6, 'b': 7},
                ops
            ),
            42
        )

    def test_short_circuit(self):
        """
        Control structures don't eval depth-first
        """
        ops = dict(JSONLOGIC_BUILTINS)
        conditions = []
        consequences = []

        def push_if(data, v):
            conditions.append(v)
            return v

        def push_then(data, v):
            consequences.append(v)
            return v

        def push_else(data, v):
            consequences.append(v)
            return v

        ops['push.if']   = push_if
        ops['push.then'] = push_then
        ops['push.else'] = push_else

        jsonLogic({"if": [
            {"push.if": [True]},
            {"push.then": ["first"]},
            {"push.if": [False]},
            {"push.then": ["second"]},
            {"push.else": ["third"]},
        ]}, operations=ops)

        self.assertListEqual(conditions, [True])
        self.assertListEqual(consequences, ["first"])

        conditions = []
        consequences = []
        jsonLogic({"if": [
            {"push.if": [False]},
            {"push.then": ["first"]},
            {"push.if": [True]},
            {"push.then": ["second"]},
            {"push.else": ["third"]},
        ]}, operations=ops)

        self.assertListEqual(conditions, [False, True])
        self.assertListEqual(consequences, ["second"])

        conditions = []
        consequences = []
        jsonLogic({"if": [
            {"push.if": [False]},
            {"push.then": ["first"]},
            {"push.if": [False]},
            {"push.then": ["second"]},
            {"push.else": ["third"]},
        ]}, operations=ops)

        self.assertListEqual(conditions, [False, False])
        self.assertListEqual(consequences, ["third"])

        i = []
        def push(data, arg):
            i.append(arg)
            return arg
        ops['push'] = push

        jsonLogic({"and": [{"push": [False]}, {"push": [False]}]}, operations=ops)
        self.assertListEqual(i, [False])
        i = []
        jsonLogic({"and": [{"push": [False]}, {"push": [True]}]}, operations=ops)
        self.assertListEqual(i, [False])
        i = []
        jsonLogic({"and": [{"push": [True]}, {"push": [False]}]}, operations=ops)
        self.assertListEqual(i, [True, False])
        i = []
        jsonLogic({"and": [{"push": [True]}, {"push": [True]}]}, operations=ops)
        self.assertListEqual(i, [True, True])

        i = []
        jsonLogic({"or": [{"push": [False]}, {"push": [False]}]}, operations=ops)
        self.assertListEqual(i, [False, False])
        i = []
        jsonLogic({"or": [{"push": [False]}, {"push": [True]}]}, operations=ops)
        self.assertListEqual(i, [False, True])
        i = []
        jsonLogic({"or": [{"push": [True]}, {"push": [False]}]}, operations=ops)
        self.assertListEqual(i, [True])
        i = []
        jsonLogic({"or": [{"push": [True]}, {"push": [True]}]}, operations=ops)
        self.assertListEqual(i, [True])

    def test_substr(self):
        """
        Sub-string of non-ASCII strings
        """
        self.assertEqual(jsonLogic({"substr": ["äöü", 0, -2]}), "ä")

        # can't have invalid unicode in Pytohn, so instread we get the replacement character
        ops = { **JSONLOGIC_BUILTINS, 'substr': op_substr_utf16 }
        logic = json.loads("{\"substr\": [\"\\uD80C\\uDC00\", 1]}")
        self.assertEqual(jsonLogic(logic, operations=ops), '\ufffd')

    def test_extras(self):
        self.assertEqual(jsonLogic({"zip": [[1,2,3],["a","b"]]}, operations=EXTRAS), [[1,"a"],[2,"b"]])
        # TODO: test more

class JsonLogicTests(unittest.TestCase):
    pass

def make_test(name: str, tests: list):
    def test_func(self: unittest.TestCase):
        for test in tests:
            logic, data, expected = test
            actual = jsonLogic(logic, data)
            self.assertEqual(actual, expected,
                f"Wrong value\n"
                f"     test: {json.dumps(test)}\n"
                f"    logic: {json.dumps(logic)}\n"
                f"     data: {json.dumps(data)}\n"
                f" expected: {json.dumps(expected)}\n"
                f"   actual: {json.dumps(actual)}\n"
            )
    test_func.__name__ = 'test_' + NON_IDENT.sub('_', name).strip('_')
    test_func.__doc__  = name
    return test_func

GROUPED_TESTS: List[dict] = []
group: Optional[dict] = None

for test in TESTS:
    if isinstance(test, str):
        if group:
            GROUPED_TESTS.append(group)
        group = {
            'name': test,
            'tests': [],
        }
    else:
        group['tests'].append(test) # type: ignore

for group in GROUPED_TESTS:
    name = group['name']
    func = make_test(name, group['tests'])
    setattr(JsonLogicTests, func.__name__, func)

def make_cert_test(name: str, logic: Any, assertions: list):
    def test_func(self: unittest.TestCase):
        for assertion in assertions:
            data       = assertion['data']
            expected   = assertion['expected']
            this_logic = assertion.get('certLogicExpression', logic)
            actual = certLogic(this_logic, data)
            self.assertEqual(actual, expected,
                f"Wrong value\n"
                f"    logic: {json.dumps(this_logic)}\n"
                f"     data: {json.dumps(data)}\n"
                f" expected: {json.dumps(expected)}\n"
                f"   actual: {json.dumps(actual)}\n"
            )
    test_func.__name__ = 'test_' + NON_IDENT.sub('_', name).strip('_')
    test_func.__doc__  = name
    return test_func

for group in CERTLOGIC_TESTS:
    group_name = group['name']

    class CertLogicTests(unittest.TestCase):
        pass

    CertLogicTests.__name__ = NON_IDENT.sub('_', group_name).strip('_').title() + 'Tests'
    CertLogicTests.__doc__  = group_name
    globals()[CertLogicTests.__name__] = CertLogicTests

    for test in group['cases']:
        name  = test['name']
        logic = test.get('certLogicExpression')
        assertions = test['assertions']
        func = make_cert_test(name, logic, assertions)
        setattr(CertLogicTests, func.__name__, func)

class ValidHealthDataTests(unittest.TestCase):
    pass

class InvalidHealthDataTests(unittest.TestCase):
    pass

NOW = parse_time("2021-08-17T15:10:00+02:00")
TEST_EXTRAS: Operations = dict(EXTRAS)

def mock_time_since(data=None, timestamp=None, *_ignored) -> float:
    dt = parse_time(timestamp)
    return (NOW - dt).total_seconds() * 1000

TEST_EXTRAS['timeSince'] = mock_time_since
TEST_EXTRAS['now']       = lambda *_ignored: NOW

def make_rule_test(name: str, data: JsonValue, expected: bool):
    def test_func(self: unittest.TestCase):
        actual = jsonLogic(RULE, data, TEST_EXTRAS)
        self.assertEqual(actual, expected,
            f"Wrong result\n"
            f"     data: {json.dumps(data)}\n"
            f" expected: {json.dumps(expected)}\n"
            f"   actual: {json.dumps(actual)}\n"
        )
    test_func.__name__ = 'test_' + NON_IDENT.sub('_', name).strip('_')
    test_func.__doc__  = name
    return test_func

for valid in VALID:
    func = make_rule_test(valid['name'], valid['code'], True)
    setattr(ValidHealthDataTests, func.__name__, func)

for invalid in INVALID:
    func = make_rule_test(invalid['name'], invalid['code'], False)
    setattr(InvalidHealthDataTests, func.__name__, func)

if __name__ == '__main__':
    unittest.main()
