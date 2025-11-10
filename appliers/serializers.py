"""
Serializers for appliers application.
"""
from typing import Dict, Any, Optional
from appliers.models import Applier, User


class UserSerializer:
    """
    Serializer for User model.
    """

    @staticmethod
    def to_dict(user: User) -> Dict[str, Any]:
        """
        Serialize a User instance to a dictionary.

        Args:
            user: User model instance

        Returns:
            dict: Serialized user data
        """
        return {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }


class ApplierSerializer:
    """
    Serializer for Applier model with nested User serialization.
    """

    @staticmethod
    def to_dict(applier: Applier, include_distance: bool = False) -> Dict[str, Any]:
        """
        Serialize an Applier instance to a dictionary.

        Args:
            applier: Applier model instance
            include_distance: Whether to include distance_km field (for search results)

        Returns:
            dict: Serialized applier data with nested user
        """
        # Convert Decimal to float for JSON serialization
        latitude: Optional[float] = (
            float(applier.latitude) if applier.latitude is not None else None
        )
        longitude: Optional[float] = (
            float(applier.longitude) if applier.longitude is not None else None
        )

        data = {
            "applier_id": applier.id,
            "external_id": applier.external_id,
            "qualified": applier.qualified,
            "latitude": latitude,
            "longitude": longitude,
            "user": UserSerializer.to_dict(applier.user),
            "source": applier.source,
            "created_at": applier.created_at,
        }

        # Add distance if available (for search results)
        if include_distance and hasattr(applier, "distance"):
            distance_km: float = applier.distance.km if applier.distance else 0.0
            data["distance_km"] = round(distance_km, 2)

        return data
