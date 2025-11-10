"""
Service layer for applier-related business logic.
"""
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from appliers.models import Applier


class ApplierSearchService:
    """
    Service class for searching appliers by geolocation.
    """

    @staticmethod
    def search_by_location(
        latitude: float,
        longitude: float,
        qualified: str = None,
        radius_km: float = 20.0,
    ):
        """
        Search for appliers within a specified radius of a geographic point.

        Args:
            latitude: Latitude of the search center point
            longitude: Longitude of the search center point
            qualified: Optional qualification status filter (YES, NO, PENDING)
            radius_km: Search radius in kilometers (default: 20)

        Returns:
            QuerySet: Filtered and annotated queryset of Applier objects with distance
        """
        # Create a Point for the search center (longitude, latitude order in GIS)
        search_point = Point(longitude, latitude, srid=4326)

        # Start with appliers that have location data
        queryset = Applier.objects.filter(
            location__isnull=False
        ).select_related("user")

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
    def format_applier_response(applier) -> dict:
        """
        Format an applier object into a JSON-serializable dictionary.

        Args:
            applier: Applier model instance with annotated distance

        Returns:
            dict: Formatted applier data
        """
        # Convert distance to kilometers
        distance_km = applier.distance.km if hasattr(applier, "distance") else 0

        return {
            "applier_id": applier.id,
            "external_id": applier.external_id,
            "qualified": applier.qualified,
            "latitude": float(applier.latitude) if applier.latitude else None,
            "longitude": float(applier.longitude) if applier.longitude else None,
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
