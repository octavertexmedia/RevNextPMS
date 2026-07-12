"""Optional FCM send helper. No-op unless FCM_SERVER_KEY is configured."""
import logging

from django.conf import settings

from .models import DeviceRegistration

logger = logging.getLogger(__name__)


def send_push_to_user(user, title: str, body: str, data: dict | None = None) -> int:
    """
    Send a data+notification push to all active devices for a user.
    Returns number of attempted sends. Requires FCM HTTP v1 or legacy key later;
    currently logs and returns 0 when FCM_SERVER_KEY is unset.
    """
    server_key = getattr(settings, 'FCM_SERVER_KEY', '') or ''
    tokens = list(
        DeviceRegistration.objects.filter(user=user, is_active=True).values_list('token', flat=True)
    )
    if not tokens:
        return 0
    if not server_key:
        logger.info(
            'Push skipped (no FCM_SERVER_KEY): user=%s title=%s devices=%s',
            getattr(user, 'id', None),
            title,
            len(tokens),
        )
        return 0

    # Legacy FCM HTTP endpoint — replace with HTTP v1 when service account is wired.
    try:
        import requests
    except ImportError:
        logger.warning('requests not available; cannot send FCM push')
        return 0

    sent = 0
    for token in tokens:
        try:
            resp = requests.post(
                'https://fcm.googleapis.com/fcm/send',
                headers={
                    'Authorization': f'key={server_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'to': token,
                    'notification': {'title': title, 'body': body},
                    'data': data or {},
                },
                timeout=8,
            )
            if resp.status_code == 200:
                sent += 1
            else:
                logger.warning('FCM send failed status=%s body=%s', resp.status_code, resp.text[:200])
        except Exception as exc:
            logger.warning('FCM send error: %s', exc)
    return sent


def notify_tenant_staff(tenant, title: str, body: str, data: dict | None = None) -> int:
    """Notify all active devices belonging to a tenant."""
    if tenant is None:
        return 0
    user_ids = (
        DeviceRegistration.objects.filter(tenant=tenant, is_active=True)
        .values_list('user_id', flat=True)
        .distinct()
    )
    total = 0
    from django.contrib.auth import get_user_model
    User = get_user_model()
    for uid in user_ids:
        user = User.objects.filter(id=uid).first()
        if user:
            total += send_push_to_user(user, title, body, data)
    return total
