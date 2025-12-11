#!/usr/bin/env python3
"""
Database Management Utility for AeroOps Backend
Provides commands for database operations and migrations
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the grandparent directory (project root) to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')

import django
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.contrib.auth.models import User


class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}{text}{Colors.RESET}")


def check_database_connection():
    """Check if database connection is working"""
    print_header("Database Connection Check")
    
    db_config = settings.DATABASES['default']
    
    print(f"Engine: {db_config['ENGINE']}")
    if 'postgresql' in db_config['ENGINE']:
        print(f"Database: {db_config['NAME']}")
        print(f"User: {db_config['USER']}")
        print(f"Host: {db_config['HOST']}")
        print(f"Port: {db_config['PORT']}")
    else:
        print(f"Database: {db_config['NAME']}")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print_success("Database connection successful!")
                return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False


def show_database_info():
    """Show detailed database information"""
    print_header("Database Information")
    
    db_config = settings.DATABASES['default']
    engine = db_config['ENGINE']
    
    if 'postgresql' in engine:
        try:
            with connection.cursor() as cursor:
                # PostgreSQL version
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                print(f"PostgreSQL Version: {version.split(',')[0]}\n")
                
                # Database size
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(%s))
                """, [db_config['NAME']])
                size = cursor.fetchone()[0]
                print(f"Database Size: {size}")
                
                # Number of tables
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                table_count = cursor.fetchone()[0]
                print(f"Number of Tables: {table_count}")
                
                # List all tables
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                print(f"\nTables:")
                for table in tables:
                    print(f"  - {table[0]}")
                
                # Connection info
                cursor.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE datname = %s", [db_config['NAME']])
                connections = cursor.fetchone()[0]
                print(f"\nActive Connections: {connections}")
                
        except Exception as e:
            print_error(f"Error getting database info: {e}")
    else:
        # SQLite
        import sqlite3
        db_path = db_config['NAME']
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"Database Size: {size / 1024:.2f} KB")
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = cursor.fetchall()
                print(f"Number of Tables: {len(tables)}")
                print(f"\nTables:")
                for table in tables:
                    print(f"  - {table[0]}")


def run_migrations():
    """Run Django migrations"""
    print_header("Running Migrations")
    
    try:
        print_info("Making migrations...")
        call_command('makemigrations')
        
        print_info("\nApplying migrations...")
        call_command('migrate')
        
        print_success("Migrations completed successfully!")
    except Exception as e:
        print_error(f"Migration failed: {e}")


def backup_database():
    """Backup the database"""
    print_header("Database Backup")
    
    db_config = settings.DATABASES['default']
    
    if 'postgresql' in db_config['ENGINE']:
        timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()
        backup_file = f"backup_{db_config['NAME']}_{timestamp}.sql"
        
        print_info(f"Backing up to: {backup_file}")
        
        cmd = [
            'pg_dump',
            '-h', db_config['HOST'],
            '-p', str(db_config['PORT']),
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '-f', backup_file
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        try:
            subprocess.run(cmd, env=env, check=True)
            print_success(f"Backup created: {backup_file}")
        except subprocess.CalledProcessError as e:
            print_error(f"Backup failed: {e}")
    else:
        # SQLite backup
        import shutil
        timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()
        backup_file = f"backup_db_{timestamp}.sqlite3"
        
        try:
            shutil.copy2(db_config['NAME'], backup_file)
            print_success(f"Backup created: {backup_file}")
        except Exception as e:
            print_error(f"Backup failed: {e}")


def show_user_stats():
    """Show user statistics"""
    print_header("User Statistics")
    
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    print(f"Total Users: {total_users}")
    print(f"Active Users: {active_users}")
    print(f"Staff Users: {staff_users}")
    print(f"Superusers: {superusers}")


def show_data_stats():
    """Show data statistics"""
    print_header("Data Statistics")
    
    from jobs.models import Job
    from resumes.models import Resume
    
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(status='active').count()
    total_resumes = Resume.objects.count()
    
    print(f"Total Jobs: {total_jobs}")
    print(f"Active Jobs: {active_jobs}")
    print(f"Total Resumes: {total_resumes}")


def main():
    """Main menu"""
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}Database Management Utility - AeroOps Backend{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    menu = """
    1. Check database connection
    2. Show database information
    3. Run migrations
    4. Backup database
    5. Show user statistics
    6. Show data statistics
    7. Open database shell
    8. Create superuser
    9. Run all checks
    0. Exit
    """
    
    while True:
        print(menu)
        choice = input(f"{Colors.YELLOW}Select an option: {Colors.RESET}").strip()
        
        if choice == '1':
            check_database_connection()
        elif choice == '2':
            show_database_info()
        elif choice == '3':
            run_migrations()
        elif choice == '4':
            backup_database()
        elif choice == '5':
            show_user_stats()
        elif choice == '6':
            show_data_stats()
        elif choice == '7':
            print_info("Opening database shell...")
            call_command('dbshell')
        elif choice == '8':
            print_info("Creating superuser...")
            call_command('createsuperuser')
        elif choice == '9':
            check_database_connection()
            show_database_info()
            show_user_stats()
            show_data_stats()
        elif choice == '0':
            print_info("Exiting...")
            break
        else:
            print_error("Invalid option. Please try again.")
        
        input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
