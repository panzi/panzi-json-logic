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
from json_logic.builtins import BUILTINS as JSONLOGIC_BUILTINS
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

    # TODO: more basic tests

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

if __name__ == '__main__':
    unittest.main()
