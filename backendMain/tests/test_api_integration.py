import io
import json
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User


class ApiIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Admin API key for Ninja jobs ingest (if configured)
        self.admin_api_key = ''

    def auth_headers(self, token=None):
        headers = {}
        if token:
            headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        elif self.admin_api_key:
            headers['HTTP_AUTHORIZATION'] = f'Bearer {self.admin_api_key}'
        return headers

    def test_jobs_ingest_and_list(self):
        payload = {
            'title': 'Senior Captain A320',
            'company': 'Test Airline',
            'country_code': 'IN',
            'operation_type': 'passenger',
            'posted_date': timezone.now().date().isoformat(),
            'url': 'https://example.com/job/1',
            'description': 'A senior captain position for Airbus A320 fleet.'
        }

        # Ingest
        resp = self.client.post('/api/jobs/ingest', data=json.dumps(payload), content_type='application/json', **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data.get('status'), ['created', 'updated', 'dedup-updated'])
        self.assertIn('id', data)

        # List with senior filter
        resp = self.client.get('/api/jobs/', {'senior': 'true'})
        self.assertEqual(resp.status_code, 200)
        listing = resp.json()
        self.assertIn('count', listing)
        self.assertIn('results', listing)
        # Should include our job as senior
        self.assertGreaterEqual(listing['count'], 1)

        # Advanced search shape
        resp = self.client.get('/api/jobs/advanced-search/', {'senior_only': 'true'})
        self.assertEqual(resp.status_code, 200)
        adv = resp.json()
        self.assertIn('count', adv)
        self.assertIn('results', adv)
        if adv['results']:
            item = adv['results'][0]
            self.assertIn('is_senior_position', item)
            self.assertTrue(item['is_senior_position'])

        # Stats endpoint
        resp = self.client.get('/api/jobs/stats/')
        self.assertEqual(resp.status_code, 200)
        stats = resp.json()
        for k in ['total', 'missing_operation_type', 'by_country', 'top_companies']:
            self.assertIn(k, stats)

    def test_scraper_manager_open_endpoints(self):
        # AllowAny endpoints
        resp = self.client.get('/api/scrapers/list_available_scrapers')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('scrapers', resp.json())

        resp = self.client.get('/api/scrapers/health_check')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('status', resp.json())

    def test_scraper_manager_authenticated_stats(self):
        # Create user and login to get JWT
        username = 'tester'
        password = 'pass12345'
        User.objects.create_user(username=username, password=password)
        resp = self.client.post('/api/auth/login/', data={'username': username, 'password': password}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        access = resp.json().get('access')
        self.assertTrue(access)

        # Authenticated endpoint
        resp = self.client.get('/api/scrapers/scraper_stats', **self.auth_headers(token=access))
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ['total_runs', 'completed_runs', 'failed_runs', 'success_rate']:
            self.assertIn(key, body)

    def test_resumes_upload_with_info_minimal(self):
        metadata = {
            'personal': {'fullName': 'Jane Doe', 'email': 'jane@example.com', 'phone': '+1-555-1234'},
            'education': [],
            'experience': [],
            'roles': [],
            'certificates': [],
            'licenses': [],
            'fileName': 'nofile.pdf'
        }

        resp = self.client.post('/api/upload-resume-with-info', data={'metadata': json.dumps(metadata)})
        self.assertEqual(resp.status_code, 200)
        out = resp.json()
        # Expected formatted response keys
        for k in ['id', 'filename', 'name', 'email', 'total_score']:
            self.assertIn(k, out)

    def test_resumes_upload_text_file(self):
        # Small text resume
        content = b"Pilot with 10+ years experience. ATPL. Airbus A320."
        file = io.BytesIO(content)
        file.name = 'resume.txt'

        resp = self.client.post('/api/upload-resume', data={'file': file})
        self.assertEqual(resp.status_code, 200)
        out = resp.json()
        for k in ['id', 'filename', 'email', 'total_score']:
            self.assertIn(k, out)
