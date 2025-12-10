# Generated manually to fix role check constraint

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_userprofile_is_verified_recruiter'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE user_profiles DROP CONSTRAINT IF EXISTS user_profiles_role_check;
                ALTER TABLE user_profiles ADD CONSTRAINT user_profiles_role_check 
                CHECK (role IN ('admin', 'manager', 'recruiter', 'job_seeker', 'user', 'viewer'));
            """,
            reverse_sql="""
                ALTER TABLE user_profiles DROP CONSTRAINT IF EXISTS user_profiles_role_check;
                ALTER TABLE user_profiles ADD CONSTRAINT user_profiles_role_check 
                CHECK (role IN ('admin', 'manager', 'user', 'viewer'));
            """
        ),
    ]
