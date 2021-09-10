panzi-json-logic
================

Pure Python 3 [JsonLogic](https://jsonlogic.com/) and
[CertLogic](https://github.com/ehn-dcc-development/dgc-business-rules/blob/main/certlogic/specification/README.md)
implementation.

There are already other JsonLogic implementations in Python, but last I looked
they don't emulate all the JavaScript operator behaviors quite right and they
don't implement CertLogic at all.

Remarks
-------

There is currently one known way where this implementation differs from the
[JavaScript implementation](https://github.com/jwadhams/json-logic-js/) of
JsonLogic: The `substr` operator in this implementation operates on code points,
but in json-logic-js it operates on UTF-16 code units. To emulate this in
Python I would need to do an UTF-16 encode/decode round-trip in `substr`, and
even then there are differences where Python disallows broken UTF-16, but
JavaScript allows it.

But if you really want the JavaScript behavior this library provides an
alternative `substr` implementation that does the UTF-16 round-trip. You can use
it like this:

```Python
from json_logic import jsonLogic
from json_logic.builtins import BUILTINS, op_substr_utf16

result = jsonLogic(logic, data, { **BUILTINS, 'substr': op_substr_utf16 })
```

TODO
----

* (more) documentation
* even more testing (it already passes the JsonLogic and CertLogic test suites)
* pypi package
