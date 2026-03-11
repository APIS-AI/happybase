"""
HappyBase utility helpers.

Internal-facing helpers used across the HappyBase package.
"""

from __future__ import annotations

import re
from collections import OrderedDict

__all__ = [
    "camel_case_to_pep8",
    "pep8_to_camel_case",
    "thrift_attrs",
    "thrift_type_to_dict",
    "ensure_bytes",
    "bytes_increment",
    "OrderedDict",
]

# ---------------------------------------------------------------------------
# Name conversion helpers
# ---------------------------------------------------------------------------

_CAMEL_TO_PEP8_RE = re.compile(r"([A-Z])")


def camel_case_to_pep8(name: str) -> str:
    """Convert a camelCase or CamelCase name to pep8_lower_case."""
    # Insert underscore before every uppercase letter, then lower-case all.
    converted = _CAMEL_TO_PEP8_RE.sub(r"_\1", name).lower()
    # Strip a leading underscore that appears when the first char was upper.
    return converted.lstrip("_")


def pep8_to_camel_case(name: str, initial: bool = False) -> str:
    """Convert a pep8_lower_case name to camelCase or CamelCase.

    If *initial* is True the first character is capitalised (CamelCase /
    UpperCamelCase); otherwise it is left lower-case.
    """
    parts = name.split("_")
    # Capitalise every part after the first unconditionally.
    result = parts[0] + "".join(p.capitalize() for p in parts[1:])
    if initial:
        result = result[0].upper() + result[1:] if result else result
    return result


# ---------------------------------------------------------------------------
# Thrift object helpers
# ---------------------------------------------------------------------------

def thrift_attrs(obj_or_cls: object) -> list[str]:
    """Return the list of Thrift attribute names for *obj_or_cls*.

    Thrift-generated classes expose their field names via the class-level
    ``thrift_spec`` tuple.  Each entry is either *None* (a gap in the field
    id sequence) or a tuple whose third element is the field name.
    """
    if isinstance(obj_or_cls, type):
        cls = obj_or_cls
    else:
        cls = type(obj_or_cls)

    spec = getattr(cls, "thrift_spec", None)
    if spec is None:
        return []

    attrs: list[str] = []
    for item in spec:
        if item is not None:
            attrs.append(item[2])
    return attrs


def thrift_type_to_dict(obj: object) -> dict[str, object]:
    """Convert a Thrift object to a plain ``dict`` keyed by field name."""
    return {attr: getattr(obj, attr) for attr in thrift_attrs(obj)}


# ---------------------------------------------------------------------------
# Bytes helpers
# ---------------------------------------------------------------------------

def ensure_bytes(str_or_bytes: object) -> bytes:
    """Return *str_or_bytes* as ``bytes``.

    * ``bytes`` values are returned unchanged.
    * ``str`` values are UTF-8 encoded.
    * Any other type raises ``TypeError``.
    """
    if isinstance(str_or_bytes, bytes):
        return str_or_bytes
    if isinstance(str_or_bytes, str):
        return str_or_bytes.encode("utf-8")
    raise TypeError(
        f"expected str or bytes, got {type(str_or_bytes).__name__!r}"
    )


def bytes_increment(b: bytes) -> bytes | None:
    """Return the lexicographically next byte string after *b*.

    Trailing ``\\xff`` bytes are stripped (carry propagation).  Returns
    ``None`` if *b* consists entirely of ``\\xff`` bytes (overflow).
    """
    # Work on a mutable copy.
    ba = bytearray(b)

    # Propagate carry from the right.
    for i in range(len(ba) - 1, -1, -1):
        if ba[i] < 0xFF:
            ba[i] += 1
            # Truncate any trailing bytes that were all 0xFF (already removed
            # by the loop stopping here).
            return bytes(ba[: i + 1])

    # All bytes were 0xFF — overflow.
    return None
