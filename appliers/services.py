"""
Service layer for applier-related business logic.
"""
import logging
from typing import Optional, Dict, Any
from decimal import Decimal

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import QuerySet

from appliers.models import Applier
from appliers.constants import WGS84_SRID, DEFAULT_SEARCH_RADIUS_KM

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

        Args:
            latitude: Latitude of the search center point (-90 to 90)
            longitude: Longitude of the search center point (-180 to 180)
            qualified: Optional qualification status filter (YES, NO, PENDING)
            radius_km: Search radius in kilometers (default: 20)

        Returns:
            QuerySet: Filtered and annotated queryset of Applier objects with distance

        Example:
            >>> results = ApplierSearchService.search_by_location(
            ...     latitude=50.94,
            ...     longitude=6.96,
            ...     qualified="YES",
            ...     radius_km=20.0
            ... )
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

        # Calculate distance, filter by radius, and sort by distance
        queryset = (
            queryset.filter(location__distance_lte=(search_point, D(km=radius_km)))
            .annotate(distance=Distance("location", search_point))
            .order_by("distance")
        )

        return queryset

    @staticmethod
    def format_applier_response(applier: Applier) -> Dict[str, Any]:
        """
        Format an applier object into a JSON-serializable dictionary.

        Args:
            applier: Applier model instance with annotated distance

        Returns:
            dict: Formatted applier data with the following structure:
                - applier_id: Primary key of the applier
                - external_id: External reference ID
                - qualified: Qualification status (YES, NO, PENDING)
                - latitude: Latitude coordinate
                - longitude: Longitude coordinate
                - distance_km: Distance from search point in kilometers
                - user: Dictionary with user information
                - source: Source information (JSON field)
                - created_at: Creation timestamp

        Example:
            >>> applier = Applier.objects.first()
            >>> formatted = ApplierSearchService.format_applier_response(applier)
            >>> print(formatted['distance_km'])
            5.23
        """
        # Convert distance to kilometers
        distance_km: float = applier.distance.km if hasattr(applier, "distance") else 0.0

        # Convert Decimal to float for JSON serialization
        latitude: Optional[float] = (
            float(applier.latitude) if applier.latitude is not None else None
        )
        longitude: Optional[float] = (
            float(applier.longitude) if applier.longitude is not None else None
        )

        return {
            "applier_id": applier.id,
            "external_id": applier.external_id,
            "qualified": applier.qualified,
            "latitude": latitude,
            "longitude": longitude,
            "distance_km": round(distance_km, 2),
            "user": {
                "user_id": applier.user.id,
                "first_name": applier.user.first_name,
                "last_name": applier.user.last_name,
                "email": applier.user.email,
            },
            "source": applier.source,
            "created_at": applier.created_at,
        }
