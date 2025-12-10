# Generated migration for production optimizations

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_create_missing_profiles'),
    ]

    operations = [
        # ====================================================================
        # JOB MODEL OPTIMIZATIONS
        # ====================================================================
        
        # Change TextField to CharField for better indexing
        migrations.AlterField(
            model_name='job',
            name='title',
            field=models.CharField(max_length=500, db_index=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='normalized_title',
            field=models.CharField(max_length=500, null=True, blank=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='company',
            field=models.CharField(max_length=200, db_index=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='location',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='source',
            field=models.CharField(max_length=50, null=True, blank=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='url',
            field=models.URLField(max_length=1000, unique=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('new', 'New'),
                    ('active', 'Active'),
                    ('reviewed', 'Reviewed'),
                    ('expired', 'Expired'),
                    ('archived', 'Archived'),
                    ('closed', 'Closed'),
                ],
                default='new',
                db_index=True
            ),
        ),
        migrations.AlterField(
            model_name='job',
            name='operation_type',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('business', 'Business'),
                    ('scheduled', 'Scheduled'),
                    ('low_cost', 'Low Cost'),
                    ('ad_hoc_charter', 'Ad-hoc Charter'),
                    ('cargo', 'Cargo'),
                    ('passenger', 'Passenger'),
                ],
                null=True,
                blank=True,
                db_index=True
            ),
        ),
        
        # Add optimized composite indexes
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['status', '-posted_date'], name='jobs_status_date_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(
                fields=['country_code', 'operation_type', '-posted_date'],
                name='jobs_country_op_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['company', '-posted_date'], name='jobs_company_date_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['source', '-created_at'], name='jobs_source_created_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(
                fields=['senior_flag', 'status', '-posted_date'],
                name='jobs_senior_status_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['-created_at'], name='jobs_created_desc_idx'),
        ),
        
        # ====================================================================
        # COMPANY MAPPING OPTIMIZATIONS
        # ====================================================================
        
        migrations.AlterField(
            model_name='companymapping',
            name='company_name',
            field=models.CharField(max_length=200, db_index=True),
        ),
        migrations.AlterField(
            model_name='companymapping',
            name='normalized_name',
            field=models.CharField(max_length=200, unique=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='companymapping',
            name='country_code',
            field=models.CharField(max_length=3, null=True, blank=True, db_index=True),
        ),
        migrations.AddField(
            model_name='companymapping',
            name='total_jobs',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='companymapping',
            name='active_jobs',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='companymapping',
            name='last_job_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='companymapping',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        
        migrations.AddIndex(
            model_name='companymapping',
            index=models.Index(fields=['normalized_name'], name='company_normalized_idx'),
        ),
        migrations.AddIndex(
            model_name='companymapping',
            index=models.Index(fields=['operation_type', '-total_jobs'], name='company_op_jobs_idx'),
        ),
        migrations.AddConstraint(
            model_name='companymapping',
            constraint=models.CheckConstraint(
                check=~models.Q(company_name=''),
                name='company_name_not_empty'
            ),
        ),
        
        # ====================================================================
        # CRAWL LOG OPTIMIZATIONS
        # ====================================================================
        
        migrations.AlterField(
            model_name='crawllog',
            name='source',
            field=models.CharField(max_length=50, db_index=True),
        ),
        migrations.AddField(
            model_name='crawllog',
            name='items_skipped',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='crawllog',
            name='items_errors',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='crawllog',
            name='execution_time',
            field=models.FloatField(null=True, blank=True, help_text='Execution time in seconds'),
        ),
        migrations.AddField(
            model_name='crawllog',
            name='success_rate',
            field=models.FloatField(null=True, blank=True, help_text='Success rate percentage'),
        ),
        migrations.AddField(
            model_name='crawllog',
            name='status',
            field=models.CharField(
                max_length=20,
                default='success',
                choices=[
                    ('success', 'Success'),
                    ('partial', 'Partial Success'),
                    ('failed', 'Failed'),
                ]
            ),
        ),
        migrations.AddField(
            model_name='crawllog',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        
        migrations.AddIndex(
            model_name='crawllog',
            index=models.Index(fields=['source', '-run_time'], name='crawl_source_time_idx'),
        ),
        migrations.AddIndex(
            model_name='crawllog',
            index=models.Index(fields=['-run_time'], name='crawl_time_desc_idx'),
        ),
        migrations.AddIndex(
            model_name='crawllog',
            index=models.Index(fields=['status', '-run_time'], name='crawl_status_time_idx'),
        ),
    ]
