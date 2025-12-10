"""
Django management command to create UserProfile for all users
This ensures every user has a profile with role assignment
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile


class Command(BaseCommand):
    help = 'Create UserProfile for all users that do not have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--role',
            type=str,
            default='user',
            help='Default role for new profiles (default: user)'
        )

    def handle(self, *args, **options):
        default_role = options['role']
        
        self.stdout.write(self.style.MIGRATE_HEADING('Creating UserProfiles...'))
        
        users_without_profile = []
        users_with_profile = 0
        
        for user in User.objects.all():
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': default_role}
            )
            
            if created:
                users_without_profile.append({
                    'username': user.username,
                    'email': user.email,
                    'role': profile.role,
                    'is_superuser': user.is_superuser
                })
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created profile for: {user.username} '
                        f'(role: {profile.role}, superuser: {user.is_superuser})'
                    )
                )
            else:
                users_with_profile += 1
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Summary:'))
        self.stdout.write(f'  Total users: {User.objects.count()}')
        self.stdout.write(
            self.style.SUCCESS(
                f'  Profiles created: {len(users_without_profile)}'
            )
        )
        self.stdout.write(f'  Already had profiles: {users_with_profile}')
        
        if users_without_profile:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Note: Newly created profiles have default role "user"'))
            self.stdout.write('You can change roles via:')
            self.stdout.write('  - Django admin: http://localhost:8000/admin/')
            self.stdout.write('  - API: POST /api/auth/users/update-role/')
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✓ All users already have profiles!'))
