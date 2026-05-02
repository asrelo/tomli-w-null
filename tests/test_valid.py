# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# SPDX-FileCopyrightText: 2026 Vyacheslav Syropyatov

from decimal import Decimal
from math import isnan
from pathlib import Path
from types import SimpleNamespace
from typing import Union, cast

import pytest
import tomli_null

import tomli_w_null
import tomli_w_null._writer

TESTS_DATA_DIR = Path(__file__).parent / "data"

V_1_0_0_COMPLIANCE_DIR = TESTS_DATA_DIR / "1.0.0" / "toml-lang-compliance" / "valid"
V_1_0_0_EXTRAS_DIR = TESTS_DATA_DIR / "1.0.0" / "extras" / "valid"

V_1_0_0_VALID_FILES = tuple(V_1_0_0_COMPLIANCE_DIR.glob("**/*.toml")) + tuple(
    V_1_0_0_EXTRAS_DIR.glob("**/*.toml")
)

V_1_1_0_EXTRAS_DIR = TESTS_DATA_DIR / "1.1.0" / "extras" / "valid"

V_1_1_0_VALID_FILES = tuple(V_1_1_0_EXTRAS_DIR.glob("**/*.toml"))


@pytest.mark.parametrize(
    "valid",
    V_1_0_0_VALID_FILES,
    ids=[p.stem for p in V_1_0_0_VALID_FILES],
)
def test_valid_v_1_0_0(valid):
    if valid.stem in {"qa-array-inline-nested-1000", "qa-table-inline-nested-1000"}:
        pytest.xfail("This much recursion is not supported")
    original_str = valid.read_bytes().decode()
    original_data = tomli_null.loads(original_str)
    dump_str = tomli_w_null.dumps(original_data)
    after_dump_data = tomli_null.loads(dump_str)
    assert replace_nans(after_dump_data) == replace_nans(original_data)


@pytest.mark.parametrize(
    "valid",
    V_1_1_0_VALID_FILES,
    ids=[p.stem for p in V_1_1_0_VALID_FILES],
)
def test_valid_v_1_1_0(valid):
    original_str = valid.read_bytes().decode()
    original_data = tomli_null.loads(original_str)
    dump_str = tomli_w_null.dumps(original_data, toml_version="1.1.0")
    after_dump_data = tomli_null.loads(dump_str)
    assert replace_nans(after_dump_data) == replace_nans(original_data)


NAN = object()


def replace_nans(cont: Union[dict, list]) -> Union[dict, list]:
    """Replace NaNs with a sentinel object to fix the problem that NaN is not
    equal to another NaN."""
    for k, v in cont.items() if isinstance(cont, dict) else enumerate(cont):
        if isinstance(v, (float, Decimal)) and isnan(v):
            cont[k] = NAN
        elif isinstance(v, dict) or isinstance(v, list):
            cont[k] = replace_nans(cont[k])
    return cont


@pytest.mark.parametrize(
    "obj,expected_str,multiline_strings",
    [
        ({"cr-newline": "foo\rbar"}, 'cr-newline = "foo\\rbar"\n', True),
        ({"crlf-newline": "foo\r\nbar"}, 'crlf-newline = """\nfoo\nbar"""\n', True),
    ],
)
def test_obj_to_str_mapping(obj, expected_str, multiline_strings):
    assert tomli_w_null.dumps(obj, multiline_strings=multiline_strings) == expected_str


@pytest.mark.parametrize(
    ("supports_escape_1_byte", "code", "expected"),
    [
        (True, 0x41, r"\x41"),
        (False, 0x41, r"\u0041"),
        (False, 0x1234, r"\u1234"),
        (False, 0x1F602, r"\U0001F602"),
        (True, 0x00, r"\x00"),
        (False, 0x00, r"\u0000"),
        (True, 0xFF, r"\xFF"),
        (False, 0xFF, r"\u00FF"),
    ],
)
def test_escape_code_as_hex(supports_escape_1_byte, code, expected):
    mock_ctx = SimpleNamespace(supports_escape_1_byte=supports_escape_1_byte)
    result = tomli_w_null._writer._escape_code_as_hex(
        code,
        cast(tomli_w_null._writer.Context, mock_ctx),
    )
    assert result.upper() == expected.upper()
