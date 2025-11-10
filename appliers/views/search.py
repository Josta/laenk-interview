from django.views import View
from django.http import JsonResponse
from appliers.services import ApplierSearchService


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
        Returns:
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

        # Use service layer for business logic
        queryset = ApplierSearchService.search_by_location(
            latitude=params["center_lat"],
            longitude=params["center_lon"],
            qualified=params["qualified"],
            radius_km=params["radius_km"],
        )

        # Format response using service layer
        data = [
            ApplierSearchService.format_applier_response(applier)
            for applier in queryset
        ]

        return JsonResponse(data, safe=False)
