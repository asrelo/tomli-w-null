# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# SPDX-FileCopyrightText: 2026 Vyacheslav Syropyatov

from collections.abc import Generator, Mapping
from datetime import date, datetime, time
from types import MappingProxyType
from typing import IO, TYPE_CHECKING, Any, Final, Union

from tomli_w_null._version import TOML_VERSION_DEFAULT, TOMLVersion

if TYPE_CHECKING:
    from decimal import Decimal


ASCII_CTRL = frozenset(chr(i) for i in range(32)) | frozenset(chr(127))
ILLEGAL_BASIC_STR_CHARS = frozenset('"\\') | ASCII_CTRL - frozenset("\t")
BARE_KEY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789" "-_"
)
ARRAY_TYPES = (list, tuple)
MAX_LINE_LENGTH = 100

BASIC_ESCAPES = MappingProxyType(
    {
        "\u0008": "\\b",  # backspace
        "\u000a": "\\n",  # linefeed
        "\u000c": "\\f",  # form feed
        "\u000d": "\\r",  # carriage return
        "\u0022": '\\"',  # quote
        "\u005c": "\\\\",  # backslash
    }
)


MULTILINE_STRINGS_DEFAULT = False
INDENT_DEFAULT = 4


class Context:
    def __init__(
        self,
        toml_version: Union[TOMLVersion, str] = TOML_VERSION_DEFAULT,
        *,
        allow_multiline: bool = MULTILINE_STRINGS_DEFAULT,
        indent: int = INDENT_DEFAULT,
    ):
        if indent < 0:
            raise ValueError("Indent width must be non-negative")
        if isinstance(toml_version, str):
            toml_version = TOMLVersion.from_string(toml_version)
        self.toml_version: Final = toml_version
        self.allow_multiline: Final = allow_multiline
        # cache rendered inline tables (mapping from object id to rendered inline table)
        self.inline_table_cache: Final[dict[int, str]] = {}
        self.indent_str: Final = " " * indent

    @property
    def supports_escape_esc(self) -> bool:
        return self.toml_version >= TOMLVersion(1, 1, 0)

    @property
    def supports_escape_1_byte(self) -> bool:
        return self.toml_version >= TOMLVersion(1, 1, 0)


def dump(
    obj: Mapping[str, "Any"],
    fp: IO[bytes],
    /,
    *,
    toml_version: Union[TOMLVersion, str] = TOML_VERSION_DEFAULT,
    multiline_strings: bool = MULTILINE_STRINGS_DEFAULT,
    indent: int = INDENT_DEFAULT,
) -> None:
    ctx = Context(toml_version, allow_multiline=multiline_strings, indent=indent)
    for chunk in gen_table_chunks(obj, ctx, name=""):
        fp.write(chunk.encode())


def dumps(
    obj: Mapping[str, Any],
    /,
    *,
    toml_version: Union[TOMLVersion, str] = TOML_VERSION_DEFAULT,
    multiline_strings: bool = MULTILINE_STRINGS_DEFAULT,
    indent: int = INDENT_DEFAULT,
) -> str:
    ctx = Context(toml_version, allow_multiline=multiline_strings, indent=indent)
    return "".join(gen_table_chunks(obj, ctx, name=""))


def gen_table_chunks(
    table: Mapping[str, Any],
    ctx: Context,
    *,
    name: str,
    inside_aot: bool = False,
) -> Generator[str, None, None]:
    yielded = False
    literals = []
    tables: list[tuple[str, Any, bool]] = []  # => [(key, value, inside_aot)]
    for k, v in table.items():
        if isinstance(v, Mapping):
            tables.append((k, v, False))
        elif is_aot(v) and not all(is_suitable_inline_table(t, ctx) for t in v):
            tables.extend((k, t, True) for t in v)
        else:
            literals.append((k, v))

    if inside_aot or name and (literals or not tables):
        yielded = True
        yield f"[[{name}]]\n" if inside_aot else f"[{name}]\n"

    if literals:
        yielded = True
        for k, v in literals:
            yield f"{format_key_part(k, ctx)} = {format_literal(v, ctx)}\n"

    for k, v, in_aot in tables:
        if yielded:
            yield "\n"
        else:
            yielded = True
        key_part = format_key_part(k, ctx)
        display_name = f"{name}.{key_part}" if name else key_part
        yield from gen_table_chunks(v, ctx, name=display_name, inside_aot=in_aot)


def format_literal(obj: object, ctx: Context, *, nest_level: int = 0) -> str:
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float, date, datetime)):
        return str(obj)
    if isinstance(obj, time):
        if obj.tzinfo:
            raise ValueError("TOML does not support offset times")
        return str(obj)
    if isinstance(obj, str):
        return format_string(obj, ctx, allow_multiline=ctx.allow_multiline)
    if isinstance(obj, ARRAY_TYPES):
        return format_inline_array(obj, ctx, nest_level)
    if isinstance(obj, Mapping):
        return format_inline_table(obj, ctx)

    # Lazy import to improve module import time
    from decimal import Decimal

    if isinstance(obj, Decimal):
        return format_decimal(obj)
    raise TypeError(
        f"Object of type '{type(obj).__qualname__}' is not TOML serializable"
    )


def format_decimal(obj: "Decimal") -> str:
    if obj.is_nan():
        return "nan"
    if obj.is_infinite():
        return "-inf" if obj.is_signed() else "inf"
    dec_str = str(obj).lower()
    return dec_str if "." in dec_str or "e" in dec_str else dec_str + ".0"


def format_inline_table(obj: Mapping, ctx: Context) -> str:
    # check cache first
    obj_id = id(obj)
    if obj_id in ctx.inline_table_cache:
        return ctx.inline_table_cache[obj_id]

    if not obj:
        rendered = "{}"
    else:
        rendered = (
            "{ "
            + ", ".join(
                f"{format_key_part(k, ctx)} = {format_literal(v, ctx)}"
                for k, v in obj.items()
            )
            + " }"
        )
    ctx.inline_table_cache[obj_id] = rendered
    return rendered


def format_inline_array(obj: Union[tuple, list], ctx: Context, nest_level: int) -> str:
    if not obj:
        return "[]"
    item_indent = ctx.indent_str * (1 + nest_level)
    closing_bracket_indent = ctx.indent_str * nest_level
    return (
        "[\n"
        + ",\n".join(
            item_indent + format_literal(item, ctx, nest_level=nest_level + 1)
            for item in obj
        )
        + f",\n{closing_bracket_indent}]"
    )


def format_key_part(part: str, ctx: Context) -> str:
    try:
        only_bare_key_chars = BARE_KEY_CHARS.issuperset(part)
    except TypeError:
        raise TypeError(
            f"Invalid mapping key '{part}' of type '{type(part).__qualname__}'."
            " A string is required."
        ) from None

    if part and only_bare_key_chars:
        return part
    return format_string(part, ctx, allow_multiline=False)


def format_string(s: str, ctx: Context, *, allow_multiline: bool) -> str:
    do_multiline = allow_multiline and "\n" in s
    if do_multiline:
        result = '"""\n'
        s = s.replace("\r\n", "\n")
    else:
        result = '"'

    pos = seq_start = 0
    while True:
        try:
            char = s[pos]
        except IndexError:
            result += s[seq_start:pos]
            if do_multiline:
                return result + '"""'
            return result + '"'
        if char in ILLEGAL_BASIC_STR_CHARS:
            result += s[seq_start:pos]
            result += escape_basic_char(char, ctx, multiline=do_multiline)
            seq_start = pos + 1
        pos += 1


def escape_basic_char(char: str, ctx: Context, *, multiline: bool) -> str:
    if multiline and char == "\n":
        return "\n"
    if char in BASIC_ESCAPES:
        return BASIC_ESCAPES[char]
    code = ord(char)
    if code == 0x1B and ctx.supports_escape_esc:
        return "\\e"
    return _escape_code_as_hex(code, ctx)


def _escape_code_as_hex(code: int, ctx: Context) -> str:
    code_hex = hex(code)[2:].upper()
    if code <= 0xFF and ctx.supports_escape_1_byte:
        return "\\x" + code_hex.rjust(2, "0")
    if code <= 0xFFFF:
        return "\\u" + code_hex.rjust(4, "0")
    return "\\U" + code_hex.rjust(8, "0")


def is_aot(obj: Any) -> bool:
    """Decides if an object behaves as an array of tables (i.e. a nonempty list
    of dicts)."""
    return bool(
        isinstance(obj, ARRAY_TYPES)
        and obj
        and all(isinstance(v, Mapping) for v in obj)
    )


def is_suitable_inline_table(obj: Mapping, ctx: Context) -> bool:
    """Use heuristics to decide if the inline-style representation is a good
    choice for a given table."""
    rendered_inline = f"{ctx.indent_str}{format_inline_table(obj, ctx)},"
    return len(rendered_inline) <= MAX_LINE_LENGTH and "\n" not in rendered_inline
