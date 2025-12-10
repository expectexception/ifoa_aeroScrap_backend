import os
import json
import tempfile
from django.test import TestCase, Client
from django.core.management import call_command
from django.conf import settings
from .models import Job, CompanyMapping
from django.contrib.auth.models import User
from django.utils import timezone
import io


class JobsBasicTests(TestCase):
    def setUp(self):
        self.client = Client()
        # configure API key for endpoints during tests
        os.environ['ADMIN_API_KEY'] = 'testkey'

    def test_health_endpoint(self):
        r = self.client.get('/api/jobs/health')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('ok', data)

    def test_ingest_and_get(self):
        payload = {
            'title': 'Test Engineer',
            'company': 'ExampleCo',
            'url': 'http://example.com/jobs/1',
            'posted_date': '2025-01-01'
        }
        r = self.client.post('/api/jobs/ingest', data=json.dumps(payload), content_type='application/json', HTTP_AUTHORIZATION='Bearer testkey')
        self.assertEqual(r.status_code, 200)
        resp = r.json()
        self.assertIn('status', resp)
        self.assertIn(resp['status'], ('created', 'updated'))
        jid = resp.get('id')
        self.assertIsNotNone(jid)

        # get job
        r2 = self.client.get(f'/api/jobs/id/{jid}')
        self.assertEqual(r2.status_code, 200)
        jdata = r2.json()
        self.assertEqual(jdata['title'], 'Test Engineer')

    def test_ingest_requires_auth(self):
        payload = {
            'title': 'Unauthorized Job',
            'company': 'NoAuthCo',
            'url': 'http://example.com/jobs/unauth',
            'posted_date': '2025-03-01'
        }
        # call without header -> should be rejected when ADMIN_API_KEY set
        r = self.client.post('/api/jobs/ingest', data=json.dumps(payload), content_type='application/json')
        self.assertIn(r.status_code, (401, 403))

    def test_management_command_ingest_from_dir(self):
        tmpdir = tempfile.mkdtemp()
        try:
            payload = {
                'title': 'Dir Job',
                'company': 'DirCo',
                'url': 'http://dir.co/job/1',
                'posted_date': '2025-02-01'
            }
            p = os.path.join(tmpdir, 'job1.json')
            with open(p, 'w') as fh:
                json.dump(payload, fh)
            # call management command
            call_command('ingest_from_dir', '--dir', tmpdir)
            # verify created
            j = Job.objects.filter(url=payload['url']).first()
            self.assertIsNotNone(j)
            self.assertEqual(j.company, 'DirCo')
        finally:
            # cleanup files
            for fname in os.listdir(tmpdir):
                try:
                    os.remove(os.path.join(tmpdir, fname))
                except Exception:
                    pass
            try:
                os.rmdir(tmpdir)
            except Exception:
                pass

    def test_jobs_advanced_and_stats(self):
            # seed a senior job via ingest
            payload = {
                'title': 'Senior Captain A320',
                'company': 'Air Demo',
                'url': 'http://demo.air/job/100',
                'posted_date': timezone.now().date().isoformat(),
                'country_code': 'IN',
                'operation_type': 'passenger',
            }
            r = self.client.post('/api/jobs/ingest', data=json.dumps(payload), content_type='application/json', HTTP_AUTHORIZATION='Bearer testkey')
            self.assertEqual(r.status_code, 200)

            # Advanced search senior_only
            r = self.client.get('/api/jobs/advanced-search/', {'senior_only': 'true'})
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertIn('count', data)
            self.assertIn('results', data)
            if data['results']:
                self.assertTrue(data['results'][0]['is_senior_position'])

            # Stats shape
            r = self.client.get('/api/jobs/stats/')
            self.assertEqual(r.status_code, 200)
            stats = r.json()
            for k in ['total', 'missing_operation_type', 'by_country', 'top_companies']:
                self.assertIn(k, stats)

    def test_scraper_manager_endpoints(self):
            # Open endpoints
            r = self.client.get('/api/scrapers/list/')
            self.assertEqual(r.status_code, 200)
            self.assertIn('scrapers', r.json())

            r = self.client.get('/api/scrapers/health/')
            self.assertEqual(r.status_code, 200)
            self.assertIn('status', r.json())

            # Authenticated stats with JWT
            u = User.objects.create_user(username='tester', password='pass12345')
            r = self.client.post('/api/auth/login/', data=json.dumps({'username': 'tester', 'password': 'pass12345'}), content_type='application/json')
            self.assertEqual(r.status_code, 200)
            token = r.json().get('access')
            self.assertTrue(token)
            r = self.client.get('/api/scrapers/stats/', HTTP_AUTHORIZATION=f'Bearer {token}')
            self.assertEqual(r.status_code, 200)
            body = r.json()
            for key in ['total_runs', 'completed_runs', 'failed_runs', 'success_rate']:
                self.assertIn(key, body)

    def test_resumes_upload_endpoints(self):
            # upload-resume-with-info without file
            meta = {
                'personal': {'fullName': 'Jane Doe', 'email': 'jane@example.com', 'phone': '+1-555-1234'},
                'education': [], 'experience': [], 'roles': [], 'certificates': [], 'licenses': [],
                'fileName': 'nofile.pdf'
            }
            r = self.client.post('/api/upload-resume-with-info', data={'metadata': json.dumps(meta)})
            self.assertEqual(r.status_code, 200)
            out = r.json()
            for k in ['id', 'filename', 'name', 'email', 'total_score']:
                self.assertIn(k, out)

            # upload-resume with a small text file
            content = b"Pilot with 10+ years experience. ATPL. Airbus A320."
            f = io.BytesIO(content)
            f.name = 'resume.txt'
            r2 = self.client.post('/api/upload-resume', data={'file': f})
            self.assertEqual(r2.status_code, 200)
            out2 = r2.json()
            for k in ['id', 'filename', 'email', 'total_score']:
                self.assertIn(k, out2)
