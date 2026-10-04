from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = 'Check the email configuration and optionally send a real test email.'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            nargs='?',
            help='Address to send a test email to. Omit to only report the configuration.',
        )
        parser.add_argument(
            '--otp',
            action='store_true',
            help='Also issue a real password reset OTP for the given account.',
        )

    def handle(self, *args, **options):
        recipient = options.get('recipient')
        console_mode = settings.EMAIL_BACKEND.endswith('console.EmailBackend')

        self.stdout.write('')
        self.stdout.write('EMAIL_BACKEND      : %s' % settings.EMAIL_BACKEND)
        self.stdout.write('EMAIL_HOST         : %s' % (settings.EMAIL_HOST or '(empty)'))
        self.stdout.write('EMAIL_PORT         : %s' % settings.EMAIL_PORT)
        self.stdout.write('EMAIL_HOST_USER    : %s' % (settings.EMAIL_HOST_USER or '(empty)'))
        self.stdout.write('EMAIL_FROM_ADDRESS : %s' % (settings.EMAIL_FROM_ADDRESS or '(empty)'))
        self.stdout.write('password configured: %s' % ('yes' if settings.EMAIL_HOST_PASSWORD else 'no'))
        self.stdout.write('')

        if console_mode:
            self.stdout.write(self.style.WARNING(
                'NO REAL EMAIL WILL BE SENT.\n'
                'The console backend prints mail to the terminal instead of delivering it,\n'
                'so nobody receives the OTP. To fix this:\n'
                '  1. https://myaccount.google.com/apppasswords  (needs 2-Step Verification on)\n'
                '  2. Put the credentials in onlinestudy/email_settings_local.py\n'
                '  3. Restart the server\n'
            ))

        if options.get('otp'):
            if not recipient:
                raise CommandError('--otp needs a recipient email that is registered.')
            user = User.objects.filter(email__iexact=recipient).first()
            if user is None:
                raise CommandError(
                    'No account uses %r. A code is never sent for an unknown address, '
                    'which is why nothing arrives if the email does not match exactly.' % recipient
                )
            from admmitions.views import _issue_otp
            _issue_otp(user)
            self.stdout.write(self.style.SUCCESS('OTP issued for %s' % user.email))

        if not recipient:
            return

        try:
            sent = send_mail(
                'Online Study - test email',
                'Your SMTP settings work. Password reset codes will arrive in this inbox.',
                settings.EMAIL_FROM_ADDRESS or None,
                [recipient],
                fail_silently=False,
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR('SEND FAILED: %s: %s' % (type(exc).__name__, exc)))
            raise CommandError('Could not send the test email.')

        if sent:
            self.stdout.write(self.style.SUCCESS('Test email sent to %s' % recipient))
            if console_mode:
                self.stdout.write('(printed to this terminal, not delivered - see warning above)')
        else:
            raise CommandError('The mail backend returned 0 messages sent.')