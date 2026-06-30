"""
Date utility for generating consistent YYYYMMDD filename prefixes.

Used by all 7 API endpoint files. Centralizing this avoids duplicating
the datetime formatting logic in every endpoint.
"""

from datetime import datetime


def date_suffix() -> str:
    """
    Returns the current date as YYYYMMDD for use in output filenames.

    Example: 20260630 for June 30, 2026.
    """
    return datetime.now().strftime("%Y%m%d")
