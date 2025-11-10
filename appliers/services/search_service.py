"""
Service layer for applier-related business logic.
"""
import logging
from typing import Optional, Dict, Any

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import QuerySet, Case, When, F, FloatField

from appliers.models import Applier
from appliers.constants import (
    WGS84_SRID,
    DEFAULT_SEARCH_RADIUS_KM,
    QUALIFIED_YES,
    QUALIFIED_PENDING,
    QUALIFIED_NO,
)

logger = logging.getLogger(__name__)


class ApplierSearchService:
    """
    Service class for searching appliers by geolocation.
    """

    @staticmethod
    def search_by_location(
        latitude: float,
        longitude: float,
        qualified: Optional[str] = None,
        radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
    ) -> QuerySet[Applier]:
        """
        Search for appliers within a specified radius of a geographic point.

        Results are sorted by a penalized distance metric that combines actual distance
        with qualification status (non-YES statuses are penalized).

        Args:
            latitude: Latitude of the search center point (-90 to 90)
            longitude: Longitude of the search center point (-180 to 180)
            qualified: Optional qualification status filter (YES, NO, PENDING)
            radius_km: Search radius in kilometers (default: 20)

        Returns:
            QuerySet: Filtered and annotated queryset of Applier objects with distance,
                     ordered by penalized distance (distance × penalty multiplier)
        """
        # Create a Point for the search center (longitude, latitude order in GIS)
        search_point = Point(longitude, latitude, srid=WGS84_SRID)

        logger.debug(
            "Performing geospatial search",
            extra={
                "latitude": latitude,
                "longitude": longitude,
                "qualified": qualified,
                "radius_km": radius_km,
            },
        )

        # Start with appliers that have location data
        queryset = Applier.objects.filter(location__isnull=False).select_related("user")

        # Filter by qualified status if provided
        if qualified:
            queryset = queryset.filter(qualified=qualified)

        # Calculate distance and create a penalty multiplier based on qualified status
        # YES: no penalty (1.0x), PENDING: (1.5x), NO: (2.0x), NULL: (3.0x)
        # This is to satisfy the requirement to sort by distance and "relevance"
        qualified_penalty = Case(
            When(qualified=QUALIFIED_YES, then=1.0),
            When(qualified=QUALIFIED_PENDING, then=1.5),
            When(qualified=QUALIFIED_NO, then=2.0),
            default=3.0,
            output_field=FloatField(),
        )

        queryset = (
            queryset.filter(location__distance_lte=(search_point, D(km=radius_km)))
            .annotate(
                distance=Distance("location", search_point),
                qualified_penalty=qualified_penalty,
                # Calculate penalized distance: actual_distance_km * penalty_multiplier
                penalized_distance=F("distance") * F("qualified_penalty"),
            )
            .order_by("penalized_distance")
        )

        return queryset
    