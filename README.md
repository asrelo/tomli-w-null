[![Build Status](https://github.com/asrelo/tomli-w-null/actions/workflows/tests.yaml/badge.svg?branch=master)](https://github.com/asrelo/tomli-w/actions?query=workflow%3ATests+branch%3Amaster+event%3Apush)

<!-- [![PyPI version](https://img.shields.io/pypi/v/tomli-w-null)](https://pypi.org/project/tomli-w-null) -->

# tomli-w-null

> A lil' TOML writer with support for non-standard `null` values (fork of `tomli-w`)

**Table of Contents** *generated with [mdformat-toc](https://github.com/hukkin/mdformat-toc)*

<!-- mdformat-toc start --slug=github --maxlevel=6 --minlevel=2 -->

- [Intro](#intro)
- [Installation](#installation)
- [Usage](#usage)
  - [Write to string](#write-to-string)
  - [Write to file](#write-to-file)
  - [Specify TOML version](#specify-toml-version)
  - [Write data with `null` values](#write-data-with-null-values)
- [FAQ](#faq)
  - [Does `tomli-w-null` sort the document?](#does-tomli-w-null-sort-the-document)
  - [Does `tomli-w-null` support writing documents with comments?](#does-tomli-w-null-support-writing-documents-with-comments)
  - [Can I customize insignificant whitespace?](#can-i-customize-insignificant-whitespace)
  - [Why does `tomli-w-null` not write a multi-line string if the string value contains newlines?](#why-does-tomli-w-null-not-write-a-multi-line-string-if-the-string-value-contains-newlines)
  - [Is `tomli-w-null` output guaranteed to be valid TOML?](#is-tomli-w-null-output-guaranteed-to-be-valid-toml)
- [License](#license)

<!-- mdformat-toc end -->

## Intro<a name="intro"></a>

`tomli-w-null` is a Python library for writing [TOML](https://toml.io),
based on [`tomli-w`](https://github/hukkin/tomli-w). It extends the writer with support
for the `null` value, mapping it from Python's `None`. All other features of `tomli-w`
are preserved. It is a write-only counterpart
to [tomli-null](https://github.com/asrelo/tomli-null), which is a read-only TOML parser.

`tomli-w-null` can produce TOML code based on TOML [v1.0.0](https://toml.io/en/v1.0.0) (default)
or [v1.1.0](https://toml.io/en/v1.1.0). Since TOML 1.1.0 is fully backwards compatible
with TOML 1.0.0 and doesn't introduce any new features in supported data structures,
TOML 1.0.0 remains the default.

## Installation<a name="installation"></a>

```bash
pip install tomli-w-null
```

## Usage<a name="usage"></a>

### Write to string<a name="write-to-string"></a>

```python
import tomli_w_null

doc = {"table": {"nested": {}, "val3": 3}, "val2": 2, "val1": 1}
expected_toml = """\
val2 = 2
val1 = 1

[table]
val3 = 3

[table.nested]
"""
assert tomli_w_null.dumps(doc) == expected_toml
```

### Write to file<a name="write-to-file"></a>

```python
import tomli_w_null

doc = {"one": 1, "two": 2, "pi": 3}
with open("path_to_file/conf.toml", "wb") as f:
    tomli_w_null.dump(doc, f)
```

### Specify TOML version<a name="specify-toml-version"></a>

```python
import tomli_w_null

doc = {"key": "value", "from_tty": "data\x04", "binary": "\x1a\x1b\x1c\x1d"}
expected_toml = """\
key = value
from_tty = "data\x04"
binary = "\x1a\e\x1c\x1d"
"""
assert tomli_w_null.dumps(doc, toml_version="1.1.0") == expected_toml
```

### Write data with `null` values<a name="write-data-with-null-values"></a>

```python
import tomli_null

doc = {"value": None, "items": [1, None, 3]}
expected_toml = """\
value = null
items = [1, null, 3]
"""
assert tomli_w_null.dumps(doc) == expected_toml
```

Python's `None` is mapped to the `null` keyword (always produced lowercase,
just like `true` / `false` in standard TOML).

## FAQ<a name="faq"></a>

### Does `tomli-w-null` sort the document?<a name="does-tomli-w-null-sort-the-document"></a>

No, but it respects sort order of the input data,
so one could sort the content of the `dict` (recursively) before calling `tomli_w_null.dumps`.

### Does `tomli-w-null` support writing documents with comments?<a name="does-tomli-w-null-support-writing-documents-with-comments"></a>

No.

### Can I customize insignificant whitespace?<a name="can-i-customize-insignificant-whitespace"></a>

Indent width of array content can be configured via the `indent` keyword argument.
`indent` takes a non-negative integer, defaulting to 4.

```python
import tomli_w_null

doc = {"fruits": ["orange", "kiwi", "papaya"]}
expected_toml = """\
fruits = [
 "orange",
 "kiwi",
 "papaya",
]
"""
assert tomli_w_null.dumps(doc, indent=1) == expected_toml
```

### Why does `tomli-w-null` not write a multi-line string if the string value contains newlines?<a name="why-does-tomli-w-null-not-write-a-multi-line-string-if-the-string-value-contains-newlines"></a>

This default was chosen to achieve lossless parse/write round-trips.

TOML strings can contain newlines where exact bytes matter, e.g.

```toml
s = "here's a newline\r\n"
```

TOML strings also can contain newlines where exact byte representation is not relevant, e.g.

```toml
s = """here's a newline
"""
```

A parse/write round-trip that converts the former example to the latter does not preserve the original newline byte sequence.
This is why Tomli-W avoids writing multi-line strings.

A keyword argument is provided for users who do not need newline bytes to be preserved:

```python
import tomli_w_null

doc = {"s": "here's a newline\r\n"}
expected_toml = '''\
s = """
here's a newline
"""
'''
assert tomli_w_null.dumps(doc, multiline_strings=True) == expected_toml
```

### Is `tomli-w-null` output guaranteed to be valid TOML?<a name="is-tomli-w-null-output-guaranteed-to-be-valid-toml"></a>

No.
If there's a chance that your input data is bad and you need output validation,
parse the output string once with `tomli.loads`.
If the parse is successful (does not raise `tomli.TOMLDecodeError`) then the string is valid TOML.

Examples of bad input data that can lead to writing invalid TOML without an error being raised include:

- A mapping where keys behave very much like strings, but aren't. E.g. a tuple of strings of length 1.
- A mapping where a value is a subclass of a supported type, but which overrides the `__str__` method.

Given proper input (a mapping consisting of non-subclassed
[types returned by Tomli](https://github.com/asrelo/tomli-null?tab=readme-ov-file#conversion-table)),
the output should be valid TOML.

## License<a name="license"></a>

`tomli-w-null` is distributed under the terms of the MIT license, see `LICENSE`.
