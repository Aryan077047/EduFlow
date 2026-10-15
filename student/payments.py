from hesabpay import on_payment_success
from hesabpay.services.webhook import process_webhook
from django.urls import reverse

from accounts.notifications import notify
from .models import CourseOrder, Enrollment


class _FakeVerifyClient:
    """Client stub whose verify_webhook_signature always passes."""

    def verify_webhook_signature(self, signature, timestamp):
        return True


@on_payment_success
def fulfill_course_payment(context):
    if not context.is_first_success:
        return
    order = context.instance
    if isinstance(order, CourseOrder):
        _, created = Enrollment.objects.get_or_create(
            student=order.student,
            course=order.course,
        )
        order.paid = True
        order.save(update_fields=['paid'])
        if created:
            course = order.course
            notify(
                order.student,
                f'You are now enrolled in "{course.title}".',
                link=reverse('user_profile'),
                kind='success',
            )
            notify(
                course.student,
                f'{order.student.get_full_name() or order.student.email} enrolled in "{course.title}".',
                link=reverse('teacher_analytics'),
            )


def simulate_hesabpay_success(order, transaction_id=None):
    """Fire the full HesabPay webhook pipeline for `order` (CourseOrder).

    Creates a pending HesabPayPayment for the order, then runs the real
    webhook processing (with signature verification stubbed out) so the
    payment_succeeded handler in this module (fulfill_course_payment)
    runs exactly as it would for a genuine HesabPay payment.
    """
    from django.contrib.contenttypes.models import ContentType
    from hesabpay.models import HesabPayPayment, PaymentStatus

    ct = ContentType.objects.get_for_model(CourseOrder)
    import time
    txn = transaction_id or f'TEST-TXN-{int(time.time() * 1000)}'
    payment = HesabPayPayment.objects.create(
        status=PaymentStatus.PENDING,
        amount=order.course.Course_price,
        currency='AFN',
        email=order.student.email,
        user=order.student,
        content_type=ct,
        object_id=str(order.pk),
        metadata={'test': 'true'},
    )
    payload = {
        'status_code': 10,
        'success': True,
        'transaction_id': txn,
        'user_id': payment.reference,
        'amount': float(order.course.Course_price),
        'signature': 'test-sig',
        'timestamp': '2026-01-01T00:00:00Z',
    }
    return process_webhook(payload, client=_FakeVerifyClient())
