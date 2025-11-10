from django.test import Client
from django.urls import reverse
from decimal import Decimal
from django.contrib.gis.geos import Point
from appliers.models import User, Applier
from appliers.tests.base import NoLoggingTestCase
import json


class SearchViewSetTestCase(NoLoggingTestCase):
    """
    Test cases for the geolocation search endpoint.
    """

    def setUp(self):
        """
        Set up test data: create users and appliers with different locations.
        Test location: Cologne, Germany (50.94, 6.96)
        """
        self.client = Client()
        self.search_url = '/api/v1/appliers/search'

        # Create test users
        self.user1 = User.objects.create(
            external_id='user1',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='+491234567890',
            resume='resumes/john.pdf',
            cover_letter='I am interested...',
            country='Germany'
        )

        self.user2 = User.objects.create(
            external_id='user2',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            phone='+491234567891',
            resume='resumes/jane.pdf',
            cover_letter='Looking forward...',
            country='Germany'
        )

        self.user3 = User.objects.create(
            external_id='user3',
            first_name='Bob',
            last_name='Johnson',
            email='bob.johnson@example.com',
            phone='+491234567892',
            resume='resumes/bob.pdf',
            cover_letter='Excited to apply...',
            country='Germany'
        )

        self.user4 = User.objects.create(
            external_id='user4',
            first_name='Alice',
            last_name='Williams',
            email='alice.williams@example.com',
            phone='+491234567893',
            resume='resumes/alice.pdf',
            cover_letter='Great opportunity...',
            country='Germany'
        )

        # Applier 1: ~0.5 km from center - QUALIFIED YES
        self.applier1 = Applier.objects.create(
            external_id='app1',
            user=self.user1,
            qualified='YES',
            latitude=Decimal('50.9413'),
            longitude=Decimal('6.9583'),
            location=Point(6.9583, 50.9413, srid=4326),
            source={'channel': 'website'}
        )

        # Applier 2: ~15 km from center - QUALIFIED NO
        self.applier2 = Applier.objects.create(
            external_id='app2',
            user=self.user2,
            qualified='NO',
            latitude=Decimal('50.8659'),
            longitude=Decimal('7.1427'),
            location=Point(7.1427, 50.8659, srid=4326),
            source={'channel': 'referral'}
        )

        # Applier 3: ~35 km from center - QUALIFIED YES
        self.applier3 = Applier.objects.create(
            external_id='app3',
            user=self.user3,
            qualified='YES',
            latitude=Decimal('51.2277'),
            longitude=Decimal('6.7735'),
            location=Point(6.7735, 51.2277, srid=4326),
            source={'channel': 'linkedin'}
        )

        # Applier 4: Near center (~2 km) - QUALIFIED PENDING
        self.applier4 = Applier.objects.create(
            external_id='app4',
            user=self.user4,
            qualified='PENDING',
            latitude=Decimal('50.9500'),
            longitude=Decimal('6.9700'),
            location=Point(6.9700, 50.9500, srid=4326),
            source={'channel': 'website'}
        )

        # Applier 5: No location data
        self.applier5 = Applier.objects.create(
            external_id='app5',
            user=self.user1,
            qualified='YES',
            latitude=None,
            longitude=None,
            source={'channel': 'website'}
        )

    def test_search_without_lat_parameter(self):
        """Test that the endpoint returns 400 when lat parameter is missing."""
        response = self.client.get(self.search_url, {'lon': '6.96'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Latitude (lat) parameter is required', data['error'])

    def test_search_without_lon_parameter(self):
        """Test that the endpoint returns 400 when lon parameter is missing."""
        response = self.client.get(self.search_url, {'lat': '50.94'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Longitude (lon) parameter is required', data['error'])

    def test_search_with_invalid_lat_parameter(self):
        """Test that the endpoint returns 400 when lat parameter is invalid."""
        response = self.client.get(self.search_url, {'lat': 'invalid', 'lon': '6.96'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Invalid latitude parameter', data['error'])

    def test_search_with_invalid_lon_parameter(self):
        """Test that the endpoint returns 400 when lon parameter is invalid."""
        response = self.client.get(self.search_url, {'lat': '50.94', 'lon': 'invalid'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Invalid longitude parameter', data['error'])

    def test_search_with_invalid_qualified_parameter(self):
        """Test that the endpoint returns 400 when qualified parameter is invalid."""
        response = self.client.get(self.search_url, {
            'lat': '50.94',
            'lon': '6.96',
            'qualified': 'INVALID'
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Invalid qualified parameter', data['error'])

    def test_search_without_qualified_filter(self):
        """Test search returns all appliers within radius, sorted by penalized distance."""
        response = self.client.get(self.search_url, {
            'lat': '50.94',
            'lon': '6.96'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should return 3 appliers within 20km (applier1, applier2, applier4)
        # Should NOT include applier3 (too far) or applier5 (no location)
        self.assertEqual(len(data), 3)

        # Check they are sorted by penalized distance:
        # app1: YES at 0.5km = 0.5 * 1.0 = 0.5 (penalized distance)
        # app4: PENDING at 2km = 2 * 1.5 = 3.0 (penalized distance)
        # app2: NO at 15km = 15 * 2.0 = 30.0 (penalized distance)
        self.assertEqual(data[0]['external_id'], 'app1')  # YES, 0.5km, penalty=0.5
        self.assertEqual(data[0]['qualified'], 'YES')
        self.assertEqual(data[1]['external_id'], 'app4')  # PENDING, 2km, penalty=3.0
        self.assertEqual(data[1]['qualified'], 'PENDING')
        self.assertEqual(data[2]['external_id'], 'app2')  # NO, 15km, penalty=30.0
        self.assertEqual(data[2]['qualified'], 'NO')

        # Verify distances are calculated
        for applier_data in data:
            self.assertIn('distance_km', applier_data)
            self.assertIsInstance(applier_data['distance_km'], (int, float))
            self.assertLessEqual(applier_data['distance_km'], 20)

    def test_search_with_qualified_yes_filter(self):
        """Test search with qualified=YES filter."""
        response = self.client.get(self.search_url, {
            'lat': '50.94',
            'lon': '6.96',
            'qualified': 'YES'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should only return applier1 (qualified=YES and within 20km)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['external_id'], 'app1')
        self.assertEqual(data[0]['qualified'], 'YES')

    def test_search_with_qualified_no_filter(self):
        """Test search with qualified=NO filter."""
        response = self.client.get(self.search_url, {
            'lat': '50.94',
            'lon': '6.96',
            'qualified': 'NO'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should only return applier2 (qualified=NO and within 20km)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['external_id'], 'app2')
        self.assertEqual(data[0]['qualified'], 'NO')

    def test_search_with_qualified_pending_filter(self):
        """Test search with qualified=PENDING filter."""
        response = self.client.get(self.search_url, {
            'lat': '50.94',
            'lon': '6.96',
            'qualified': 'PENDING'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should only return applier4 (qualified=PENDING and within 20km)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['external_id'], 'app4')
        self.assertEqual(data[0]['qualified'], 'PENDING')

    def test_search_excludes_appliers_without_location(self):
        """Test that appliers without location data are excluded."""
        response = self.client.get(self.search_url, {
            'lat': '50.94',
            'lon': '6.96',
            'qualified': 'YES'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should only return applier1, not applier5 (which also has qualified=YES but no location)
        external_ids = [item['external_id'] for item in data]
        self.assertIn('app1', external_ids)
        self.assertNotIn('app5', external_ids)

    def test_search_response_structure(self):
        """Test that the response has the correct structure."""
        response = self.client.get(self.search_url, {
            'lat': '50.94',
            'lon': '6.96'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertGreater(len(data), 0)

        # Check structure of first result
        applier_data = data[0]
        self.assertIn('applier_id', applier_data)
        self.assertIn('external_id', applier_data)
        self.assertIn('qualified', applier_data)
        self.assertIn('latitude', applier_data)
        self.assertIn('longitude', applier_data)
        self.assertIn('distance_km', applier_data)
        self.assertIn('user', applier_data)
        self.assertIn('source', applier_data)
        self.assertIn('created_at', applier_data)

        # Check user structure
        user_data = applier_data['user']
        self.assertIn('user_id', user_data)
        self.assertIn('first_name', user_data)
        self.assertIn('last_name', user_data)
        self.assertIn('email', user_data)

    def test_search_with_custom_radius(self):
        """Test search with custom radius parameter."""
        # Search with 10km radius (should exclude applier2 which is ~15km away)
        response = self.client.get(self.search_url, {
            'lat': '50.94',
            'lon': '6.96',
            'radius': '10'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should only return appliers within 10km
        self.assertEqual(len(data), 2)
        for applier_data in data:
            self.assertLessEqual(applier_data['distance_km'], 10)

    def test_search_with_no_results(self):
        """Test search that returns no results."""
        # Search in a location far from any appliers
        response = self.client.get(self.search_url, {
            'lat': '0',
            'lon': '0'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)
        self.assertEqual(data, [])

    def test_search_sorting_by_penalized_distance(self):
        """Test that results are sorted by penalized distance (distance × penalty multiplier)."""
        # Create additional test appliers to verify sorting
        user5 = User.objects.create(
            external_id='user5',
            first_name='Charlie',
            last_name='Brown',
            email='charlie@example.com',
            phone='+491234567894',
            resume='resumes/charlie.pdf',
            cover_letter='Test',
            country='Germany'
        )

        # Create appliers with different qualified status and distances
        # YES at 10km: penalized = 10 * 1.0 = 10.0
        applier6 = Applier.objects.create(
            external_id='app6',
            user=user5,
            qualified='YES',
            latitude=Decimal('50.85'),
            longitude=Decimal('6.96'),
            location=Point(6.96, 50.85, srid=4326),
            source={'channel': 'test'}
        )

        # NO at 1km: penalized = 1 * 2.0 = 2.0
        # This should come AFTER app4 (PENDING at 2km = 3.0) because 2.0 < 3.0
        applier7 = Applier.objects.create(
            external_id='app7',
            user=user5,
            qualified='NO',
            latitude=Decimal('50.9450'),
            longitude=Decimal('6.9650'),
            location=Point(6.9650, 50.9450, srid=4326),
            source={'channel': 'test'}
        )

        response = self.client.get(self.search_url, {
            'lat': '50.94',
            'lon': '6.96'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Extract external_ids and qualified status with actual distances
        results = [(item['external_id'], item['qualified'], item['distance_km']) for item in data]

        # Expected penalized distances:
        # app1: YES, 0.5km → 0.5 * 1.0 = 0.5
        # app7: NO, 1km → 1 * 2.0 = 2.0
        # app4: PENDING, 2km → 2 * 1.5 = 3.0
        # app6: YES, 10km → 10 * 1.0 = 10.0
        # app2: NO, 15km → 15 * 2.0 = 30.0

        # Verify order by external_id
        external_ids = [item['external_id'] for item in data]

        # Find positions
        app1_pos = external_ids.index('app1')
        app7_pos = external_ids.index('app7')
        app4_pos = external_ids.index('app4')
        app6_pos = external_ids.index('app6')
        app2_pos = external_ids.index('app2')

        # Verify penalized distance ordering
        self.assertLess(app1_pos, app7_pos, "app1 (penalty=0.5) should come before app7 (penalty=2.0)")
        self.assertLess(app7_pos, app4_pos, "app7 (penalty=2.0) should come before app4 (penalty=3.0)")
        self.assertLess(app4_pos, app6_pos, "app4 (penalty=3.0) should come before app6 (penalty=10.0)")
        self.assertLess(app6_pos, app2_pos, "app6 (penalty=10.0) should come before app2 (penalty=30.0)")

        # Key insight: NO at 1km (penalty=2.0) ranks better than PENDING at 2km (penalty=3.0)
        # This demonstrates the merged metric working correctly
