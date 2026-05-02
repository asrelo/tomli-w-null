# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# SPDX-FileCopyrightText: 2026 Vyacheslav Syropyatov

import pytest

from tomli_w_null import TOMLVersion


@pytest.mark.parametrize(
    ("major", "minor", "patch"),
    [(0, 0, 0), (1, 2, 3), (10, 0, 5)],
)
def test_valid_construction(major, minor, patch):
    v = TOMLVersion(major, minor, patch)
    assert (v.major, v.minor, v.patch) == (major, minor, patch)


@pytest.mark.parametrize("args", [(-1, 0, 0), (0, -5, 0), (0, 0, -10)])
def test_negative_parts_raise(args):
    with pytest.raises(ValueError):
        _ = TOMLVersion(*args)


@pytest.mark.parametrize(
    ("s", "expected"),
    [("0.0.0", (0, 0, 0)), ("1.2.3", (1, 2, 3)), ("12.34.56", (12, 34, 56))],
)
def test_from_string_valid(s, expected):
    v = TOMLVersion.from_string(s)
    assert (v.major, v.minor, v.patch) == expected


@pytest.mark.parametrize("s", ["1.2", "1.2.3.4", "a.b.c", "1.-2.3", "", " 1.2.3 "])
def test_from_string_invalid(s):
    with pytest.raises(ValueError):
        _ = TOMLVersion.from_string(s)


def test_comparison_objects():
    a = TOMLVersion(1, 0, 0)
    b = TOMLVersion(1, 0, 1)
    c = TOMLVersion(1, 2, 0)
    d = TOMLVersion(2, 0, 0)
    assert a < b < c < d
    assert d > c > b > a
    assert a <= a
    assert d >= d


@pytest.mark.parametrize(
    ("obj", "string", "expected_eq", "expected_lt"),
    [
        (TOMLVersion(1, 0, 0), "1.0.0", True, False),
        (TOMLVersion(1, 0, 1), "1.0.0", False, False),
        (TOMLVersion(0, 9, 9), "1.0.0", False, True),
    ],
)
def test_comparison_with_string(obj, string, expected_eq, expected_lt):
    a = TOMLVersion(1, 0, 0)
    b = TOMLVersion(1, 0, 1)
    c = "1.2.0"
    d = "2.0.0"
    assert a < b < c < d
    assert d > c > b > a
    assert a <= a
    assert d >= d


def test_comparison_invalid_type():
    v = TOMLVersion(1, 2, 3)
    assert (v == 123) is False
    with pytest.raises(TypeError):
        _ = v < 140


def test_hash_and_equality_consistency():
    a = TOMLVersion(3, 4, 5)
    b = TOMLVersion.from_string("3.4.5")
    assert a == b
    assert hash(a) == hash(b)


def test_str_and_repr():
    v = TOMLVersion(7, 8, 9)
    s = str(v)
    r = repr(v)
    assert s == "7.8.9"
    assert r == f"TOMLVersion({s!r})"
    assert v == s
    reconstructed = TOMLVersion.from_string(s)
    assert reconstructed == v
