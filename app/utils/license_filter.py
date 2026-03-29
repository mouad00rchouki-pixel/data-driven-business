"""Simple license compliance helpers.

The challenge wants a commercial-use filter. We keep the rule intentionally
simple and conservative:

- allow clearly permissive licenses
- block clearly restrictive licenses
- if the license is missing or unclear, treat it as not safe for commercial use
"""

from __future__ import annotations


ALLOWED_COMMERCIAL_LICENSE_KEYWORDS = [
    "apache",
    "mit",
    "bsd",
    "mpl",
    "cc-by",
    "llama",
    "openrail",
    "commercial",
    "proprietary",
]

DISALLOWED_COMMERCIAL_LICENSE_KEYWORDS = [
    "non-commercial",
    "non commercial",
    "research only",
    "research",
    "personal",
    "academic",
    "nc",
    "not for commercial",
]


def is_commercially_allowed(license_type: str | None) -> bool:
    """Return True only if the license looks commercially usable."""

    if not license_type:
        return False

    normalized_license = license_type.strip().lower()

    for blocked_keyword in DISALLOWED_COMMERCIAL_LICENSE_KEYWORDS:
        if blocked_keyword in normalized_license:
            return False

    for allowed_keyword in ALLOWED_COMMERCIAL_LICENSE_KEYWORDS:
        if allowed_keyword in normalized_license:
            return True

    # Conservative rule:
    # If we cannot confidently identify the license as permissive, exclude it.
    return False


def filter_records_for_commercial_use(records: list[dict]) -> list[dict]:
    """Keep only records that pass the commercial-use rule."""

    return [
        record
        for record in records
        if is_commercially_allowed(record.get("license_type"))
    ]
