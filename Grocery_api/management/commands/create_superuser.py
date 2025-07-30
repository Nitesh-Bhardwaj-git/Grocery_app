from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a superuser for the admin panel'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Username for superuser')
        parser.add_argument('--email', type=str, default='admin@example.com', help='Email for superuser')
        parser.add_argument('--password', type=str, default='admin123', help='Password for superuser')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists')
            )
            return

        user = User.objects.create_superuser(username, email, password)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created superuser "{username}"')
        ) 