from django.views import View
from django.http import JsonResponse
from django.db import connection


class SearchViewSet(View):
    """
    Search endpoint for finding appliers within a specified radius of a geolocation.
    Uses PostGIS ST_Distance function for efficient spatial queries.

    Query parameters:
    - lat (required): Latitude of the search center point
    - lon (required): Longitude of the search center point
    - qualified (optional): Filter by qualification status (YES, NO, PENDING)
    - radius (optional): Search radius in kilometers (default: 20km)
    """

    def get(self, request, *args, **kwargs):
        # Get query parameters
        try:
            lat = request.GET.get("lat")
            lon = request.GET.get("lon")

            if lat is None or lon is None:
                return JsonResponse(
                    {"error": "Both lat and lon parameters are required"}, status=400
                )

            center_lat = float(lat)
            center_lon = float(lon)
        except (ValueError, TypeError):
            return JsonResponse(
                {"error": "Invalid lat or lon parameters. Must be valid numbers."},
                status=400,
            )

        qualified = request.GET.get("qualified")
        radius_km = float(request.GET.get("radius", 20))

        # Validate qualified parameter
        if qualified:
            qualified_upper = qualified.upper()
            if qualified_upper not in ["YES", "NO", "PENDING"]:
                return JsonResponse(
                    {
                        "error": "Invalid qualified parameter. Must be YES, NO, or PENDING."
                    },
                    status=400,
                )
        else:
            qualified_upper = None

        # Use PostGIS ST_Distance to calculate distances efficiently
        # Use a subquery to calculate distance once and filter/sort on it
        sql = """
            SELECT
                id,
                external_id,
                qualified,
                latitude,
                longitude,
                source,
                created_at,
                user_id,
                first_name,
                last_name,
                email,
                distance_km
            FROM (
                SELECT
                    a.id,
                    a.external_id,
                    a.qualified,
                    a.latitude,
                    a.longitude,
                    a.source,
                    a.created_at,
                    u.id as user_id,
                    u.first_name,
                    u.last_name,
                    u.email,
                    ST_Distance(
                        ST_MakePoint(a.longitude, a.latitude)::geography,
                        ST_MakePoint(%s, %s)::geography
                    ) / 1000.0 as distance_km
                FROM appliers_applier a
                INNER JOIN appliers_user u ON a.user_id = u.id
                WHERE
                    a.latitude IS NOT NULL
                    AND a.longitude IS NOT NULL
        """

        params = [center_lon, center_lat]

        # Add qualified filter if provided
        if qualified_upper:
            sql += " AND a.qualified = %s"
            params.append(qualified_upper)

        # Close the subquery and filter by radius, then sort by distance
        sql += """
            ) as subquery
            WHERE distance_km <= %s
            ORDER BY distance_km ASC
        """
        params.append(radius_km)

        # Execute the query
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Format response
        data = []
        for row in results:
            data.append(
                {
                    "applier_id": row["id"],
                    "external_id": row["external_id"],
                    "qualified": row["qualified"],
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "distance_km": round(float(row["distance_km"]), 2),
                    "user": {
                        "user_id": row["user_id"],
                        "first_name": row["first_name"],
                        "last_name": row["last_name"],
                        "email": row["email"],
                    },
                    "source": row["source"],
                    "created_at": row["created_at"],
                }
            )

        return JsonResponse(data, safe=False)
