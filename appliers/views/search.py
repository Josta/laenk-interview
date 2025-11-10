import logging
from typing import Dict, List

from django.views import View
from django.http import JsonResponse, HttpRequest
from appliers.services.search_service import ApplierSearchService
from appliers.forms.search import ApplierSearchForm
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

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        Handle GET request for applier search.

        Args:
            request: Django HTTP request object

        Returns:
            JsonResponse: List of matching appliers with distance information
        """
        # Parse and validate parameters
        form = ApplierSearchForm(request.GET)
        if not form.is_valid():
            return JsonResponse({"error": form.get_error_message}, status=400)

        params = {
            "latitude": form.cleaned_data["lat"],
            "longitude": form.cleaned_data["lon"],
            "qualified": form.cleaned_data["qualified"],
            "radius_km": form.cleaned_data["radius"],
        }

        queryset = ApplierSearchService.search_by_location(
            latitude=params["latitude"],
            longitude=params["longitude"],
            qualified=params["qualified"],
            radius_km=params["radius_km"],
        )

        data: List[Dict] = [
            ApplierSerializer.to_dict(applier, include_distance=True) for applier in queryset
        ]

        logger.info(
            "Applier search",
            extra={"result_count": {"params": params, "results": len(data)}},
        )

        return JsonResponse(data, safe=False)
