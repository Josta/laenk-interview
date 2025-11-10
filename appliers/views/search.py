import logging
from typing import Dict, List, Optional, Tuple

from django.views import View
from django.http import JsonResponse, HttpRequest
from appliers.services import ApplierSearchService
from appliers.forms import ApplierSearchForm
from appliers.serializers import ApplierSerializer

logger = logging.getLogger(__name__)


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

    def _parse_and_validate_params(
        self, request: HttpRequest
    ) -> Tuple[Optional[Dict[str, float | str | None]], Optional[JsonResponse]]:
        """
        Parse and validate GET parameters using Django forms.

        Args:
            request: Django HTTP request object

        Returns:
            tuple: (params_dict, error_response)
                - params_dict: Dictionary with validated parameters if successful, None if error
                - error_response: JsonResponse with error if validation fails, None if successful
        """
        form = ApplierSearchForm(request.GET)

        if not form.is_valid():
            # Extract first error message from form errors
            errors = form.errors.as_data()
            first_error_field = next(iter(errors))
            first_error = errors[first_error_field][0]
            error_message = first_error.message

            logger.warning(
                "Invalid search parameters",
                extra={
                    "errors": form.errors.get_json_data(),
                    "params": dict(request.GET),
                },
            )

            return None, JsonResponse({"error": error_message}, status=400)

        cleaned_data = form.cleaned_data
        params = {
            "center_lat": cleaned_data["lat"],
            "center_lon": cleaned_data["lon"],
            "qualified": cleaned_data["qualified"],
            "radius_km": cleaned_data["radius"],
        }

        return params, None

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        Handle GET request for applier search.

        Args:
            request: Django HTTP request object

        Returns:
            JsonResponse: List of matching appliers with distance information
        """
        # Parse and validate parameters
        params, error_response = self._parse_and_validate_params(request)
        if error_response:
            return error_response

        logger.info(
            "Applier search request",
            extra={
                "latitude": params["center_lat"],
                "longitude": params["center_lon"],
                "qualified": params["qualified"],
                "radius_km": params["radius_km"],
            },
        )

        # Use service layer for business logic
        queryset = ApplierSearchService.search_by_location(
            latitude=params["center_lat"],
            longitude=params["center_lon"],
            qualified=params["qualified"],
            radius_km=params["radius_km"],
        )

        # Format response using service layer
        data: List[Dict] = [
            ApplierSerializer.to_dict(applier, include_distance=True) for applier in queryset
        ]

        logger.info(
            "Applier search completed",
            extra={"result_count": len(data), "radius_km": params["radius_km"]},
        )

        return JsonResponse(data, safe=False)
