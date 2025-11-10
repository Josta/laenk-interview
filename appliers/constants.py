"""
Constants for appliers application.
"""

# Qualified status choices
QUALIFIED_YES = "YES"
QUALIFIED_NO = "NO"
QUALIFIED_PENDING = "PENDING"

QUALIFIED_CHOICES = [
    QUALIFIED_YES,
    QUALIFIED_NO,
    QUALIFIED_PENDING,
]

# Search parameters
DEFAULT_SEARCH_RADIUS_KM = 20.0
MIN_RADIUS_KM = 0.1
MAX_RADIUS_KM = 100.0

# Geographic constants
WGS84_SRID = 4326  # World Geodetic System 1984 coordinate reference system