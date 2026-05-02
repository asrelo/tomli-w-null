# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Vyacheslav Syropyatov

from functools import total_ordering
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import re
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


@total_ordering
class TOMLVersion:

    _PATTERN = None  # built lazily using _build_pattern

    @classmethod
    def _get_pattern(cls) -> "re.Pattern":
        if cls._PATTERN is None:
            import re  # lazy import

            cls._PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
        return cls._PATTERN

    def __init__(self, major: int, minor: int, patch: int):
        if major < 0:
            raise ValueError(
                "every part of the version number must be greater or equal to 0"
            )
        if minor < 0:
            raise ValueError(
                "every part of the version number must be greater or equal to 0"
            )
        if patch < 0:
            raise ValueError(
                "every part of the version number must be greater or equal to 0"
            )
        self.major: Final = major
        self.minor: Final = minor
        self.patch: Final = patch

    @classmethod
    def from_string(cls, version_str: str) -> "Self":
        m = cls._get_pattern().match(version_str)
        if not m:
            raise ValueError(f"Invalid TOML version: {version_str!r}")
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    def _sort_key(self) -> tuple:
        return (self.major, self.minor, self.patch)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            other = TOMLVersion.from_string(other)
        if not isinstance(other, TOMLVersion):
            return NotImplemented
        return self._sort_key() == other._sort_key()

    def __lt__(self, other: object) -> bool:
        if isinstance(other, str):
            other = TOMLVersion.from_string(other)
        if not isinstance(other, TOMLVersion):
            return NotImplemented
        return self._sort_key() < other._sort_key()

    def __hash__(self) -> int:
        return hash(self._sort_key())

    def __str__(self) -> str:
        return ".".join(map(str, (self.major, self.minor, self.patch)))

    def __repr__(self) -> str:
        return f"TOMLVersion({str(self)!r})"


TOML_VERSION_DEFAULT: Final = TOMLVersion(1, 0, 0)
