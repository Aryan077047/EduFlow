from django.apps import AppConfig


class AdmmitionsConfig(AppConfig):
    name = 'admmitions'

    def ready(self):
        # Register HesabPay payment-success handler (creates Enrollment after payment).
        try:
            from . import payments  # noqa: F401
        except Exception:
            pass
