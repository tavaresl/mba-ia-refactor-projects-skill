import logging
import smtplib

from utils.dates import utc_now

logger = logging.getLogger(__name__)


class NotificationService:
    """Envio de e-mails. Host, credenciais e fábrica de SMTP são injetados."""

    def __init__(self, host, port, user, password, smtp_factory=smtplib.SMTP):
        self.notifications = []
        self.email_host = host
        self.email_port = port
        self.email_user = user
        self.email_password = password
        self._smtp_factory = smtp_factory

    @classmethod
    def from_settings(cls, settings):
        return cls(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
        )

    def send_email(self, to, subject, body):
        try:
            server = self._smtp_factory(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logger.info("Email enviado para %s", to)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception("Erro ao enviar email")
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você."
            f"\n\nPrioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utc_now(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!"
            f"\n\nData limite: {task.due_date}"
        )
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
