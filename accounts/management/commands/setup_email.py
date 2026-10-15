import getpass
import os

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError

LOCAL_SETTINGS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    'onlinestudy',
    'email_settings_local.py',
)

PROVIDERS = {
    '1': ('smtp.gmail.com', 587, 'Gmail'),
    '2': ('smtp-mail.outlook.com', 587, 'Outlook / Hotmail'),
    '3': ('smtp.mail.yahoo.com', 587, 'Yahoo'),
}

TEMPLATE = '''"""
Local SMTP credentials for the OTP password reset. Written by
`python manage.py setup_email`. Gitignored - never commit this file.

Auto-generated, safe to delete and regenerate at any time.
"""

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = '{host}'
EMAIL_PORT = {port}
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 20

EMAIL_HOST_USER = '{user}'
EMAIL_HOST_PASSWORD = '{password}'

EMAIL_FROM_ADDRESS = '{user}'
'''


class Command(BaseCommand):
    help = 'Interactively configure SMTP so password reset codes reach a real inbox.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Only report the current configuration, change nothing.',
        )

    def handle(self, *args, **options):
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Email configuration'))
        self.stdout.write('  backend       : %s' % settings.EMAIL_BACKEND)
        self.stdout.write('  host          : %s' % (settings.EMAIL_HOST or '(none)'))
        self.stdout.write('  user          : %s' % (settings.EMAIL_HOST_USER or '(none)'))
        self.stdout.write('  password set  : %s' % ('yes' if settings.EMAIL_HOST_PASSWORD else 'no'))
        self.stdout.write('  from address  : %s' % (settings.EMAIL_FROM_ADDRESS or '(none)'))
        self.stdout.write('')

        if options.get('check'):
            return

        if not sys_is_interactive():
            raise CommandError(
                'setup_email needs to prompt for the app password, so it must be run from a '
                'terminal. In PowerShell:  python manage.py setup_email'
            )

        self.stdout.write(self.style.MIGRATE_HEADING('Step 1 - which mailbox sends the codes?'))
        self.stdout.write('  1) Gmail        smtp.gmail.com:587')
        self.stdout.write('  2) Outlook      smtp-mail.outlook.com:587')
        self.stdout.write('  3) Yahoo        smtp.mail.yahoo.com:587')
        choice = input('Provider [1]: ').strip() or '1'
        if choice not in PROVIDERS:
            raise CommandError('Pick 1, 2 or 3.')
        host, port, label = PROVIDERS[choice]

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Step 2 - credentials'))
        self.stdout.write('Your normal account password will NOT work. %s needs an' % label)
        self.stdout.write('app password / app-specific password instead:')
        self.stdout.write('  Gmail   https://myaccount.google.com/apppasswords   (2-Step Verification required)')
        self.stdout.write('  Outlook https://account.microsoft.com/security-settings/')
        self.stdout.write('  Yahoo   https://login.yahoo.com/account/security')
        self.stdout.write('')

        address = input('Mailbox address that sends the codes: ').strip()
        if '@' not in address:
            raise CommandError('That does not look like an email address.')

        password = getpass.getpass('App password (input hidden): ').strip().replace(' ', '')
        if not password:
            raise CommandError('The app password cannot be empty.')

        previous = read_previous_password()
        write_file(host, port, address, password)

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Step 3 - testing the connection'))

        # Apply immediately so the test uses the new values, no restart needed.
        reload_email_settings(host, port, address, password)

        try:
            send_mail(
                '%s - setup complete' % settings.OTP_EMAIL_SENDER_NAME,
                'Password reset codes will arrive in this inbox.\n\n'
                'Your address is %s.' % address,
                address,
                [address],
                fail_silently=False,
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR('  FAILED: %s: %s' % (type(exc).__name__, exc)))
            self.stderr.write('')
            for line in explain(exc):
                self.stderr.write('  %s' % line)
            if previous is None:
                write_empty()
                self.stdout.write(self.style.WARNING(
                    '  Credentials cleared, so nothing is broken. Try again once the app '
                    'password is right.'
                ))
            raise CommandError('Setup failed - no working configuration was saved.')

        self.stdout.write(self.style.SUCCESS('  Sent a test email to %s' % address))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Saved to onlinestudy/email_settings_local.py'))
        self.stdout.write('Check that inbox (and spam) for the test message, then restart the')
        self.stdout.write('dev server. Codes will now be emailed instead of shown on the page.')


def sys_is_interactive():
    import sys
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except Exception:
        return False


def write_file(host, port, address, password):
    with open(LOCAL_SETTINGS, 'w', encoding='utf-8') as handle:
        handle.write(TEMPLATE.format(host=host, port=port, user=address, password=password))


def write_empty():
    with open(LOCAL_SETTINGS, 'w', encoding='utf-8') as handle:
        handle.write(TEMPLATE.format(
            host='smtp.gmail.com', port=587, user='', password='',
        ))


def read_previous_password():
    """Best-effort read so a failed setup can be rolled back."""
    try:
        namespace = {}
        with open(LOCAL_SETTINGS, encoding='utf-8') as handle:
            exec(handle.read(), namespace)  # noqa: S102 - our own generated file
        return namespace.get('EMAIL_HOST_PASSWORD') or None
    except Exception:
        return None


def reload_email_settings(host, port, address, password):
    """Point the running process at the new backend without a restart."""
    from django.core.mail import get_connection
    settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    settings.EMAIL_HOST = host
    settings.EMAIL_PORT = port
    settings.EMAIL_USE_TLS = True
    settings.EMAIL_TIMEOUT = 20
    settings.EMAIL_HOST_USER = address
    settings.EMAIL_HOST_PASSWORD = password
    settings.EMAIL_FROM_ADDRESS = address
    settings.EMAIL_CONSOLE_MODE = False
    import django.core.mail as mail_module
    mail_module.get_connection = get_connection
    send_mail.connection = None


def explain(exc):
    text = str(exc).lower()
    if 'authentication' in text or '535' in text:
        return [
            'The server rejected the address or app password.',
            '- Check the app password was copied in full (16 characters for Gmail).',
            '- Confirm 2-Step Verification is ON before creating an app password.',
            '- Some accounts block SMTP until "Less secure app access" is allowed.',
        ]
    if 'timed out' in text or 'connection' in text:
        return [
            'Could not reach the mail server.',
            '- Check your internet connection and any firewall.',
            '- Some networks block outbound port 587; try port 465 with SSL instead.',
        ]
    return ['Review the message above and try again.']