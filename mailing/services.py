import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Mailing, MailingAttempt

logger = logging.getLogger(__name__)


def send_mailing(mailing_id):
    """
    Отправляет рассылку по её ID.
    """
    try:
        mailing = Mailing.objects.get(id=mailing_id)
    except Mailing.DoesNotExist:
        logger.error(f"Рассылка с ID {mailing_id} не найдена.")
        return False

    if mailing.status != "running":
        logger.info(f"Рассылка {mailing_id} не в статусе 'running'. Пропускаем.")
        return False

    from django.utils import timezone

    now = timezone.now()
    if mailing.first_send_time > now:
        logger.info(f"Время отправки рассылки {mailing_id} ещё не наступило.")
        return False
    if mailing.end_time < now:
        logger.info(f"Время окончания рассылки {mailing_id} уже прошло.")
        mailing.status = "completed"  # Можно автоматически завершать
        mailing.save()
        return False

    message = mailing.message
    clients = mailing.clients.all()

    if not clients.exists():
        logger.warning(f"В рассылке {mailing_id} нет клиентов.")
        return False

    success_count = 0
    failure_count = 0

    for client in clients:
        try:
            send_mail(
                subject=message.subject,
                message=message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                fail_silently=False,
            )

            MailingAttempt.objects.create(
                mailing=mailing,
                status="success",
                server_response=f"Письмо успешно отправлено на {client.email}",
            )
            success_count += 1
            logger.info(f"Письмо отправлено: {client.email}")

        except Exception as e:

            error_msg = f"Ошибка отправки на {client.email}: {e}"
            MailingAttempt.objects.create(
                mailing=mailing, status="failed", server_response=error_msg
            )
            failure_count += 1
            logger.error(error_msg)

    logger.info(
        f"Рассылка {mailing_id} завершена. Успешно: {success_count}, Ошибок: {failure_count}"
    )
    return True
