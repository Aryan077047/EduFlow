"""Helpers for the header notification bell."""

from django.urls import reverse

from .models import Notification


def notify(user, message, link='', kind='info'):
    """Create a notification for `user`. `link` must be an internal path."""
    if user is None or not getattr(user, 'pk', None):
        return None
    if link and not link.startswith('/'):
        link = ''
    return Notification.objects.create(
        user=user, message=message[:255], link=link[:255], kind=kind,
    )


def notify_many(users, message, link='', kind='info'):
    if link and not link.startswith('/'):
        link = ''
    Notification.objects.bulk_create([
        Notification(user=u, message=message[:255], link=link[:255], kind=kind)
        for u in users if getattr(u, 'pk', None)
    ])


def serialize(notification):
    return {
        'id': notification.id,
        'message': notification.message,
        'link': notification.link,
        'kind': notification.kind,
        'is_read': notification.is_read,
        'created_at': notification.created_at.isoformat(),
        'read_url': reverse('notification_read', args=[notification.id]),
    }


def notifications_context_processor(request):
    """Unread count for the header badge, rendered server-side."""
    user = getattr(request, 'user', None)
    if not getattr(user, 'is_authenticated', False):
        return {}
    return {
        'notif_unread_count': Notification.objects.filter(
            user=user, is_read=False,
        ).count(),
    }
