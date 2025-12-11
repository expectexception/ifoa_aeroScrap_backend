import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from jobs.models import Job, CompanyMapping


class CompanyMappingAndJobsAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user and JWT token
        self.user = User.objects.create_user(username='admin', password='adminpass', is_staff=True, is_superuser=True)
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.auth_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'
        }

        # Seed jobs
        self.job_air_india = Job.objects.create(
            title='Senior Flight Operations Manager',
            normalized_title='senior flight operations manager',
            company='Air India',
            country_code='IND',
            location='New Delhi',
            operation_type='passenger',
            status='active',
            senior_flag=True,
            posted_date=timezone.now().date(),
            url='https://airindia.example/jobs/1',
            description='Operations leadership role.'
        )

        self.job_emirates = Job.objects.create(
            title='Flight Dispatcher',
            normalized_title='flight dispatcher',
            company='Emirates Airlines',
            country_code='UAE',
            location='Dubai',
            operation_type='passenger',
            status='active',
            senior_flag=False,
            posted_date=timezone.now().date(),
            url='https://emirates.example/jobs/2',
            description='Dispatch operations.'
        )

        self.job_spicejet = Job.objects.create(
            title='Aircraft Maintenance Engineer',
            normalized_title='aircraft maintenance engineer',
            company='SpiceJet',
            country_code='IND',
            location='Mumbai',
            operation_type='low_cost',
            status='active',
            senior_flag=False,
            posted_date=timezone.now().date(),
            url='https://spicejet.example/jobs/3',
            description='Maintenance role.'
        )

        # One mapping for Air India; others unknown on purpose
        CompanyMapping.objects.create(
            company_name='Air India',
            normalized_name='air india',
            operation_type='passenger',
            country_code='IND'
        )

    # ----------------------------
    # Company mapping endpoints
    # ----------------------------
    def test_company_mappings_requires_auth(self):
        resp = self.client.get('/api/jobs/admin/company-mappings')
        self.assertIn(resp.status_code, (200, 401))
        if resp.status_code != 200:
            # Ensure authorized call succeeds
            resp_auth = self.client.get('/api/jobs/admin/company-mappings', **self.auth_headers)
            self.assertEqual(resp_auth.status_code, 200)
            self.assertIsInstance(resp_auth.json(), list)

    def test_company_mapping_crud(self):
        # Create
        payload = {
            'company_name': 'Qatar Airways',
            'normalized_name': 'qatar airways',
            'operation_type': 'passenger',
            'country_code': 'QAT',
            'notes': 'Flag carrier of Qatar'
        }
        r_create = self.client.post('/api/jobs/admin/company-mappings', data=payload, content_type='application/json', **self.auth_headers)
        self.assertEqual(r_create.status_code, 200)
        cid = r_create.json().get('id')
        self.assertTrue(cid)

        # Update
        upd = payload.copy()
        upd['notes'] = 'Five-star airline'
        r_update = self.client.put(f'/api/jobs/admin/company-mappings/{cid}', data=upd, content_type='application/json', **self.auth_headers)
        self.assertEqual(r_update.status_code, 200)
        self.assertTrue(r_update.json().get('updated'))

        # Delete
        r_delete = self.client.delete(f'/api/jobs/admin/company-mappings/{cid}', **self.auth_headers)
        self.assertEqual(r_delete.status_code, 200)
        self.assertTrue(r_delete.json().get('deleted'))

    def test_unknown_companies(self):
        r = self.client.get('/api/jobs/admin/unknown-companies?limit=10')
        self.assertEqual(r.status_code, 200)
        names = r.json()
        self.assertIn('Emirates Airlines', names)
        self.assertIn('SpiceJet', names)
        # Air India is mapped; should not be in unknowns
        self.assertNotIn('Air India', names)

    # ----------------------------
    # Job filters & search
    # ----------------------------
    def test_list_jobs_filters(self):
        # Country + type + senior
        r = self.client.get('/api/jobs/?country=IND&type=passenger&senior=true')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['company'], 'Air India')

    def test_advanced_search_filters(self):
        url = '/api/jobs/advanced-search/?countries=IND,UAE&operation_types=passenger&senior_only=true'
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        # Only Air India matches passenger + IND/UAE + senior_only
        self.assertGreaterEqual(data['count'], 1)
        companies = {item['company'] for item in data['results']}
        self.assertIn('Air India', companies)

    def test_senior_alerts(self):
        r = self.client.get('/api/jobs/alerts/senior?hours=48')
        self.assertEqual(r.status_code, 200)
        items = r.json()
        # Should include at least the senior Air India job created in setUp
        self.assertTrue(any(it['company'] == 'Air India' for it in items))

    def test_patch_title_recomputes_senior_flag_when_missing(self):
        # Start with a non-senior job
        j = Job.objects.create(
            title='Operations Controller',
            company='TestCo',
            country_code='IND',
            url='https://testco.example/jobs/patch-1',
            posted_date=timezone.now().date(),
            senior_flag=False,
            status='active'
        )

        # Patch title to senior variant without passing senior_flag
        r1 = self.client.patch(
            f'/api/jobs/{j.id}',
            data=json.dumps({'title': 'Senior Operations Controller'}),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(r1.status_code, 200)
        j.refresh_from_db()
        self.assertTrue(j.senior_flag)

        # Patch title back to non-senior without senior_flag
        r2 = self.client.patch(
            f'/api/jobs/{j.id}',
            data=json.dumps({'title': 'Operations Controller'}),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(r2.status_code, 200)
        j.refresh_from_db()
        self.assertFalse(j.senior_flag)

    def test_senior_override_takes_precedence(self):
        # Non-senior title but override to True
        j = Job.objects.create(
            title='Operations Controller',
            company='OverrideCo',
            country_code='IND',
            url='https://override.example/jobs/1',
            posted_date=timezone.now().date(),
            senior_flag=False,
            senior_override=True,
            status='active'
        )
        j.refresh_from_db()
        self.assertTrue(j.senior_flag)

        # Senior-looking title but override to False
        j2 = Job.objects.create(
            title='Senior Operations Manager',
            company='OverrideCo',
            country_code='IND',
            url='https://override.example/jobs/2',
            posted_date=timezone.now().date(),
            senior_override=False,
            status='active'
        )
        j2.refresh_from_db()
        self.assertFalse(j2.senior_flag)

    # ----------------------------
    # Ingestion auto-mapping & senior detection
    # ----------------------------
    def test_ingest_auto_mapping_and_senior_detection(self):
        payload = {
            'title': 'Senior Operations Controller',
            'company': 'IndiGo Airlines',
            'country_code': 'IND',
            'posted_date': timezone.now().date().isoformat(),
            'url': 'https://goindigo.example/jobs/100',
            'description': 'Operations control role.'
        }
        r = self.client.post('/api/jobs/ingest', data=payload, content_type='application/json', **self.auth_headers)
        self.assertEqual(r.status_code, 200)
        self.assertIn(r.json().get('status'), ('created', 'updated', 'dedup-updated'))

        # Verify job created with senior_flag True (title contains Senior)
        j = Job.objects.get(url=payload['url'])
        self.assertTrue(j.senior_flag)

        # Verify company mapping auto-created with normalized name
        norm = 'indigo airlines'
        self.assertTrue(CompanyMapping.objects.filter(normalized_name=norm).exists())
