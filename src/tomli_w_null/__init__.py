# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen

__all__ = ("dumps", "dump", "TOMLVersion", "TOML_VERSION_DEFAULT")
__version__ = "1.0.1"  # DO NOT EDIT THIS LINE MANUALLY. LET bump2version UTILITY DO IT

from tomli_w_null._version import TOML_VERSION_DEFAULT, TOMLVersion
from tomli_w_null._writer import dump, dumps
