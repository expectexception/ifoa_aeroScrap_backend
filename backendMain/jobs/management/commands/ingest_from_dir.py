import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from django.utils import timezone

from jobs.models import Job, CompanyMapping
from jobs import utils


class Command(BaseCommand):
    help = 'Ingest job JSON files from a directory into the database'

    def add_arguments(self, parser):
        parser.add_argument('--dir', required=True, help='Directory containing JSON files')
        parser.add_argument('--source', required=False, default='airflow', help='Source name to set on ingested jobs')
        parser.add_argument('--delete-after', action='store_true', help='Delete files after successful ingest')

    def handle(self, *args, **options):
        d = Path(options['dir'])
        source = options['source']
        delete_after = options['delete_after']

        if not d.exists() or not d.is_dir():
            self.stderr.write(f"Directory not found: {d}")
            return

        files = list(d.glob('*.json'))
        total = 0
        created = 0
        updated = 0
        errors = 0

        for f in files:
            try:
                with open(f, 'r') as fh:
                    data = json.load(fh)

                # data may be a list or an object
                items = data if isinstance(data, list) else [data]
                for payload in items:
                    total += 1
                    try:
                        fields = {}
                        mapping = [
                            'title', 'normalized_title', 'company', 'company_id', 'country_code',
                            'operation_type', 'posted_date', 'url', 'description', 'status',
                            'senior_flag', 'source', 'last_checked', 'raw_json'
                        ]
                        for k in mapping:
                            if k in payload:
                                fields[k] = payload[k]

                        if 'posted_date' in fields and isinstance(fields['posted_date'], str):
                            try:
                                fields['posted_date'] = parse_date(fields['posted_date'])
                            except Exception:
                                fields['posted_date'] = None

                        if 'raw_json' in fields and isinstance(fields['raw_json'], dict):
                            raw = fields['raw_json']
                        else:
                            raw = payload
                        fields['raw_json'] = raw

                        if not fields.get('operation_type'):
                            op = utils.classify_company_by_name(fields.get('company'))
                            if op:
                                fields['operation_type'] = op

                        if 'title' in fields and 'senior_flag' not in fields:
                            fields['senior_flag'] = utils.is_senior(fields.get('title'))

                        fields['source'] = source

                        # upsert by url
                        url = fields.get('url')
                        if url:
                            try:
                                job = Job.objects.get(url=url)
                                for k, v in fields.items():
                                    if k in [f.name for f in Job._meta.fields]:
                                        setattr(job, k, v)
                                job.save()
                                updated += 1
                                continue
                            except Job.DoesNotExist:
                                pass

                        # dedupe by company/title/date
                        title = fields.get('title')
                        company = fields.get('company')
                        posted_date = fields.get('posted_date')
                        possible = Job.objects.filter(company__iexact=company)
                        found_dup = False
                        for p in possible:
                            if utils.is_duplicate(p.title, p.company, p.posted_date, title, company, posted_date):
                                for k, v in fields.items():
                                    if k in [f.name for f in Job._meta.fields]:
                                        setattr(p, k, v)
                                p.save()
                                updated += 1
                                found_dup = True
                                break
                        if found_dup:
                            continue

                        # create
                        create_kwargs = {k: v for k, v in fields.items() if k in [f.name for f in Job._meta.fields]}
                        Job.objects.create(**create_kwargs)
                        created += 1

                    except Exception as e:
                        errors += 1
                        self.stderr.write(f"Error ingesting payload from {f}: {e}")

                if delete_after:
                    try:
                        os.remove(f)
                    except Exception:
                        pass

            except Exception as e:
                errors += 1
                self.stderr.write(f"Error reading file {f}: {e}")

        self.stdout.write(f"Ingest complete: total={total} created={created} updated={updated} errors={errors}")
