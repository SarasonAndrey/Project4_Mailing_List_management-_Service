from celery import shared_task
from .services import send_mailing
from .models import Mailing
from django.utils import timezone

@shared_task
def send_scheduled_mailings():
    """
    Задача Celery для отправки активных рассылок.
    Вызывается по расписанию через Celery Beat.
    """
    now = timezone.now()

    mailings_to_send = Mailing.objects.filter(
        status__in=['created', 'running'],
        first_send_time__lte=now,
        end_time__gte=now
    )

    sent_count = 0
    for mailing in mailings_to_send:
        success = send_mailing(mailing.id)
        if success:
            sent_count += 1

            if mailing.status == 'created':
                mailing.status = 'running'
                mailing.save()

    return f"Отправлено {sent_count} рассылок."


@shared_task
def send_single_mailing(mailing_id):
    """
    Задача Celery для отправки одной рассылки по ID.
    Вызывается из интерфейса.
    """
    return send_mailing(mailing_id)