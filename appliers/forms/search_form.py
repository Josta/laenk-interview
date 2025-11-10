import logging
from django import forms
from appliers.constants import (
    QUALIFIED_CHOICES,
    DEFAULT_SEARCH_RADIUS_KM,
    MIN_RADIUS_KM,
    MAX_RADIUS_KM,
)

logger = logging.getLogger(__name__)

class ApplierSearchForm(forms.Form):
    """
    Form for validating applier search parameters.

    Validates:
    - lat: Required latitude coordinate (-90 to 90)
    - lon: Required longitude coordinate (-180 to 180)
    - qualified: Optional qualification status (YES, NO, PENDING)
    - radius: Optional search radius in kilometers (default: 20km)
    """

    lat = forms.FloatField(
        required=True,
        min_value=-90.0,
        max_value=90.0,
        error_messages={
            'required': 'Latitude (lat) parameter is required',
            'invalid': 'Invalid latitude parameter. Must be a valid number between -90 and 90.',
            'min_value': 'Latitude must be between -90 and 90 degrees.',
            'max_value': 'Latitude must be between -90 and 90 degrees.',
        }
    )

    lon = forms.FloatField(
        required=True,
        min_value=-180.0,
        max_value=180.0,
        error_messages={
            'required': 'Longitude (lon) parameter is required',
            'invalid': 'Invalid longitude parameter. Must be a valid number between -180 and 180.',
            'min_value': 'Longitude must be between -180 and 180 degrees.',
            'max_value': 'Longitude must be between -180 and 180 degrees.',
        }
    )

    qualified = forms.ChoiceField(
        required=False,
        choices=[(choice, choice) for choice in QUALIFIED_CHOICES],
        error_messages={
            'invalid_choice': f'Invalid qualified parameter. Must be one of: {", ".join(QUALIFIED_CHOICES)}.',
        }
    )

    radius = forms.FloatField(
        required=False,
        initial=DEFAULT_SEARCH_RADIUS_KM,
        min_value=MIN_RADIUS_KM,
        max_value=MAX_RADIUS_KM,
        error_messages={
            'invalid': 'Invalid radius parameter. Must be a valid number.',
            'min_value': f'Radius must be at least {MIN_RADIUS_KM} km.',
            'max_value': f'Radius must not exceed {MAX_RADIUS_KM} km.',
        }
    )

    def clean_qualified(self) -> str | None:
        """Normalize qualified parameter to uppercase."""
        qualified = self.cleaned_data.get('qualified')
        if qualified:
            return qualified.upper()
        return None

    def clean_radius(self) -> float:
        """Return radius or default value."""
        radius = self.cleaned_data.get('radius')
        return radius if radius is not None else DEFAULT_SEARCH_RADIUS_KM

    def get_error_message(self) -> str:
        # Extract first error message from form errors
        errors = self.errors.as_data()
        first_error_field = next(iter(errors))
        first_error = errors[first_error_field][0]
        error_message = first_error.message

        logger.warning(
            "Invalid search parameters",
            extra={
                "errors": self.errors.get_json_data()
            },
        )