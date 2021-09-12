panzi-json-logic
================

Pure Python 3 [JsonLogic](https://jsonlogic.com/) and
[CertLogic](https://github.com/ehn-dcc-development/dgc-business-rules/blob/main/certlogic/specification/README.md)
implementation.

The JsonLogic format is designed to allow you to share rules (logic) between
front-end and back-end code (regardless of language difference), even to store
logic along with a record in a database. JsonLogic is documented at
[JsonLogic.com](http://jsonlogic.com), including examples of every
[supported operation](http://jsonlogic.com/operations.html) and a place to
[try out rules in your browser](http://jsonlogic.com/play.html).

CertLogic is a dialect of JsonLogic with slightly different semantics and
operations.

There are already other JsonLogic implementations in Python, but last I looked
they don't emulate all the JavaScript operator behaviors quite right and they
don't implement CertLogic at all. This implementation tries to be as close to
the [JavaScript implementation](https://github.com/jwadhams/json-logic-js) of
JsonLogic as feasible.

I've also written a JsonLogic+CertLogic implementation written in C:
[jsonlogic-c](https://github.com/panzi/jsonlogic-c)

* [Installation](#installation)
* [Examples](#examples)
  * [Simple](#simple)
  * [Compound](#compound)
  * [Data-Driven](#data-driven)
  * [Always and Never](#always-and-never)
  * [CertLogic](#certlogic)
* [Custom Operations](#custom-operations)
* [Extras](#extras)
* [Remarks](#remarks)
* [Credits](#credits)

Installation
------------

Install this package via pypi:

```bash
pip install panzi-json-logic
```

Examples
--------

### Simple

```python
from json_logic import jsonLogic
jsonLogic( { "==" : [1, 1] } )
# True
```

This is a simple test, equivalent to `1 == 1`. A few things about the format:

1. The operator is always in the "key" position. There is only one key per
   JsonLogic rule.
2. The values are typically an array.
3. Each value can be a string, number, boolean, array (non-associative), or null

Note that `==` tries to emulate the JavaScript `==` operator and as such it is
adviseable to rather use `===`, which in this implementations simply uses
Python's `==`.

### Compound

Here rules are nested.

```Python
jsonLogic(
  { "and" : [
    { ">" : [3, 1] },
    { "<" : [1, 3] }
  ] }
)
# True
```

In an infix language (like Python) this could be written as:

```Python
( (3 > 1) and (1 < 3) )
```

### Data-Driven

Obviously these rules aren't very interesting if they can only take static
literal data. Typically `jsonLogic()` will be called with a rule object and a
data object. You can use the `var` operator to get attributes of the data object:

```Python
jsonLogic(
  { "var" : ["a"] }, # Rule
  { a : 1, b : 2 }   # Data
)
# 1
```

If you like, [syntactic sugar](https://en.wikipedia.org/wiki/Syntactic_sugar)
on unary operators to skip the array around values is supported:

```Python
jsonLogic(
  { "var" : "a" },
  { a : 1, b : 2 }
)
# 1
```

You can also use the `var` operator to access an array by numeric index:

```Python
jsonLogic(
  { "var" : 1 },
  [ "apple", "banana", "carrot" ]
)
# "banana"
```

Here's a complex rule that mixes literals and data. The pie isn't ready to eat
unless it's cooler than 110 degrees, *and* filled with apples.

```Python
rules = { "and" : [
  { "<" : [ { "var" : "temp" }, 110 ]},
  { "==" : [ { "var" : "pie.filling" }, "apple" ] }
] }

data = { "temp" : 100, "pie" : { "filling" : "apple" } }

jsonLogic(rules, data)
# True
```

### Always and Never

Sometimes the rule you want to process is "Always" or "Never." If the first
parameter passed to `jsonLogic()` is a non-object, non-associative-array, it is
returned immediately.

```Python
# Always
jsonLogic(True, data_will_be_ignored)
# True

# Never
jsonLogic(False, i_wasnt_even_supposed_to_be_here)
# False
```

### CertLogic

CertLogic is implemented in the `json_logic.cert_logic` sub-module:

```Python
from json_logic.cert_logic import certLogic

certLogic({
    "plusTime": [
        "2022-01-02T15:00:00+02:00",
        2,
        "day"
    ]
}).isoformat()
# '2022-01-04T15:00:00+02:00'
```

Custom Operations
-----------------

In contrast to other JsonLogic implementations you are not supposed to
manipulate the libraries dictionary of operations, but instead pass your own
dictionary as optional 3rd argument to `jsonLogic()`. If you want to use
the predefined operations you have to manually include them:

```Python
from json_logic import jsonLogic
from json_logic.builtins import BUILTINS

ops = { **BUILTINS, 'pow': lambda data, a, b: a ** b }
jsonLogic({ 'pow': [3, 2]}, None, ops)
# 9
```

Note that in contrast to other Python JsonLogic libraries the data as passed to
the `jsonLogic()` function (or the context data in
`map`/`filter`/`reduce`/`all`/`some`/`none`) is passed to operator functions as
the first argument (you can call it `self` if you want to, to be consistent with
the JavaScript implementation where it is the `this` argument).

Note that not all operations can be overwritten with the operations dictionary.
In particular these operations are hard coded in because of their short circuit
behavior or because they execute one operand on all the items of a list: `if`
(alternative spelling: `?:`), `and`, `or`, `map`, `filter`, `reduce`, `all`,
`some`, `none`.

The `certLogic()` function can be called in the same way with extra operations.
The CertLogic builtins can be found under `json_logic.cert_logic.builtins.BUILTINS`.

Extras
------

This library also includes some extra operators that are not part of JsonLogic.
You can find them under `json_logic.extras.EXTRAS`. This dictionary already
includes `json_logic.builtins.BUILTINS`. The same extras but combined with
`json_logic.cert_logic.builtins.BUILTINS` can be found under
`json_logic.cert_logic.extras.EXTRAS`. The CertLogic extras also include all the
operations from JsonLogic that are otherwise missing from CertLogic, but with
CertLogic semantics for `!` and `!!` (i.e. empty objects are falsy in CertLogic,
but truthy in JsonLogic).

### `now`

Retrieve current time as Python `datetime` object in UTC.

```
{
    "now": []
}
```

Example:

```Python
from json_logic import jsonLogic
from json_logic.extras import EXTRAS
jsonLogic({"now":[]}, None, EXTRAS)
# datetime.datetime(2021, 9, 12, 0, 31, 25, 419443, tzinfo=datetime.timezone.utc)
```

### `parseTime`

Parse RFC 3339 date and date-time strings. Date-time strings without an explicit
time zone offset are assumed to be in UTC. Note that a RFC 3339 is a subset of
ISO 8601, but it is actually what most people think of when they think of ISO
date-time strings.

```
{
    "parseTime": [
        <string-or-datetime>
    ]
}
```

Example:

```Python
jsonLogic({"parseTime":"2022-01-02"}, None, EXTRAS)
# datetime.datetime(2022, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
jsonLogic({"parseTime":"2022-01-02T15:00:00+02:00"}, None, EXTRAS)
# datetime.datetime(2022, 1, 2, 15, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)))
```

**NOTE:**

You need to use `parseTime` before comparing actual `datetime` objects with
date-times provided as a string or you'll get wrong results. Assume the current
time is somewhen in 2021:

```Python
jsonLogic({"<": [{"now":[]},"2022-01-02"]}, None, EXTRAS)
# False
jsonLogic({"<": [{"now":[]},{"parseTime":"2022-01-02"}]}, None, EXTRAS)
# True
```

However CertLogic has operators that are doing that for you:

```Python
from json_logic import certLogic
from json_logic.cert_logic.extras import EXTRAS
certLogic({"before":[{"now":[]},"2022-01-02"]}, None, EXTRAS)
# True
```

Note that `json_logic.cert_logic.extras.EXTRAS` (to get `now`) is used with
`certLogic`.

### `formatTime`

Format `date`/`datetime` object (or date-time encoded as a string) as a RFC 3339
string.

```
{
    "formatTime": [
        <string-or-datetime>
    ]
}
```

Example:

```Python
certLogic({'formatTime':{'now':''}}, None, EXTRAS)
# '2021-09-12T01:03:56.534319+00:00'
```

### `timeSince`

Milliseconds since given date-time.

```
{
    "timeSince": [
        <string-or-datetime>
    ]
}
```

Exmaple:

```Python
jsonLogic({"timeSince":"2021-01-02T15:00:00+02:00"}, None, EXTRAS)
# 21814538195.281
```

### `hours`

Convert hours to milliseconds. Useful in combination with `timeSince`.

```
{
    "hours": [
        <number>
    ]
}
```

Example:

```Python
jsonLogic({"hours": 2}, None, EXTRAS)
# 7200000
```

### `days`

Convert days to milliseconds. Useful in combination with `timeSince`.

```
{
    "hours": [
        <number>
    ]
}
```

Example:

```Python
jsonLogic({"days": 2}, None, EXTRAS)
# 172800000
```

### `combinations`

Return array of arrays that represent all combinations of the elements of all
the lists.

```
{
    "combinations": [
        <array>...
    ]
}
```

Example:

```Python
from json_logic import jsonLogic
from json_logic.extras import EXTRAS

jsonLogic({"combinations": [
    [1, 2, 3],
    ["a", "b", "c"],
    ["x", "y", "z"],
]}, None, EXTRAS)
# [[1, 'a'], [1, 'b'], [2, 'a'], [2, 'b']]
```

### `zip`

Like Python's `zip()`, but returns array of arrays (instead of generator of
tuples).

```
{
    "zip": [
        <array>...
    ]
}
```

Example:

```Python
jsonLogic({"zip": [
    [1, 2],
    ["a", "b"],
]}, None, EXTRAS)
# [[1, 'a'], [2, 'b']]
```

Remarks
-------

There is currently one known way where this implementation differs from the
[JavaScript implementation](https://github.com/jwadhams/json-logic-js/) of
JsonLogic: The `substr` operator in this implementation operates on code points,
but in json-logic-js it operates on UTF-16 code units. To emulate this in
Python an UTF-16 encode/decode round-trip is needed in `substr`, and even then
there are differences where Python disallows broken UTF-16, but JavaScript
allows it.

But if you really want the JavaScript behavior this library provides an
alternative `substr` implementation that does the UTF-16 round-trip. You can use
it like this:

```Python
from json_logic import jsonLogic
from json_logic.builtins import BUILTINS, op_substr_utf16

result = jsonLogic(logic, data, { **BUILTINS, 'substr': op_substr_utf16 })
```

Credits
-------

Some of this README is copied from [json-logic-py](https://github.com/nadirizr/json-logic-py),
some of the tests are ported from [json-logic-js](https://github.com/jwadhams/json-logic-js)
and the [JsonLogic test suite](https://jsonlogic.com/tests.json) and the
[CertLogic test suite](https://github.com/ehn-dcc-development/dgc-business-rules/tree/main/certlogic/specification/testSuite)
are included in the tests of this library.
