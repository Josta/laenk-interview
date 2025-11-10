from django.views import View
from django.http import JsonResponse
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from appliers.models import Applier


class SearchViewSet(View):
    """
    Search endpoint for finding appliers within a specified radius of a geolocation.
    Uses GeoDjango's ORM with PostGIS for efficient spatial queries.

    Query parameters:
    - lat (required): Latitude of the search center point
    - lon (required): Longitude of the search center point
    - qualified (optional): Filter by qualification status (YES, NO, PENDING)
    - radius (optional): Search radius in kilometers (default: 20km)
    """

    def _parse_and_validate_params(self, request):
        """
        Parse and validate GET parameters.

        Args:
            request: Django request object

        Returns:
            tuple: (params_dict, error_response)
                - params_dict: Dictionary with validated parameters if successful, None if error
                - error_response: JsonResponse with error if validation fails, None if successful
        """
        # Validate and parse latitude
        lat = request.GET.get("lat")
        lon = request.GET.get("lon")

        if lat is None or lon is None:
            return None, JsonResponse(
                {"error": "Both lat and lon parameters are required"}, status=400
            )

        try:
            center_lat = float(lat)
            center_lon = float(lon)
        except (ValueError, TypeError):
            return None, JsonResponse(
                {"error": "Invalid lat or lon parameters. Must be valid numbers."},
                status=400,
            )

        # Validate and parse qualified parameter
        qualified = request.GET.get("qualified")
        qualified_upper = None
        if qualified:
            qualified_upper = qualified.upper()
            if qualified_upper not in ["YES", "NO", "PENDING"]:
                return None, JsonResponse(
                    {
                        "error": "Invalid qualified parameter. Must be YES, NO, or PENDING."
                    },
                    status=400,
                )

        # Parse radius parameter
        try:
            radius_km = float(request.GET.get("radius", 20))
        except (ValueError, TypeError):
            return None, JsonResponse(
                {"error": "Invalid radius parameter. Must be a valid number."},
                status=400,
            )

        params = {
            "center_lat": center_lat,
            "center_lon": center_lon,
            "qualified": qualified_upper,
            "radius_km": radius_km,
        }

        return params, None

    def get(self, request):
        # Parse and validate parameters
        params, error_response = self._parse_and_validate_params(request)
        if error_response:
            return error_response

        center_lat = params["center_lat"]
        center_lon = params["center_lon"]
        qualified_upper = params["qualified"]
        radius_km = params["radius_km"]

        # Create a Point for the search center (longitude, latitude order in GIS)
        search_point = Point(center_lon, center_lat, srid=4326)

        # Query using GeoDjango's spatial lookups and functions
        queryset = Applier.objects.filter(
            location__isnull=False
        ).select_related("user")

        # Filter by qualified status if provided
        if qualified_upper:
            queryset = queryset.filter(qualified=qualified_upper)

        # Calculate distance and filter by radius
        # Using D() for distance measurement (km=kilometers)
        queryset = queryset.filter(
            location__distance_lte=(search_point, D(km=radius_km))
        ).annotate(
            distance=Distance("location", search_point)
        ).order_by("distance")

        # Format response
        data = []
        for applier in queryset:
            # Convert distance to kilometers
            distance_km = applier.distance.km if applier.distance else 0

            data.append(
                {
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
            )

        return JsonResponse(data, safe=False)
