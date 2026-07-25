from email.message import EmailMessage
import aiosmtplib
from core.config import settings
from core.logging_system import logger
import ssl
import certifi


class EmailService:
    """Сервис для асинхронной отправки писем через Mail.ru SMTP"""

    def __init__(self):
        self.smtp_server = settings.MAIL_SERVER
        self.smtp_port = settings.MAIL_PORT
        self.username = settings.MAIL_USERNAME
        self.password = settings.MAIL_PASSWORD
        self.from_email = settings.MAIL_FROM

    async def send_text_email(self, to_email: str, text: str):
        """ Отправка текста на указанную почту """
        message = EmailMessage()
        message["From"] = f"Сервис по бронирования номеров отелей <{self.from_email}>"
        message["To"] = to_email
        message["Subject"] = " Вам пришло сообщение по бронированию отелей. "
        message.set_content(text)

        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            # Для порта 465 use_tls=True
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=True,  # Для Mail.ru SSL (465)
                tls_context=ssl_context,
                timeout=10,
            )
            logger.info(f"[EmailService] Сообщение успешно отправлено на {to_email}")
            return True

        except Exception as e:
            logger.error(f"[EmailService] Ошибка отправки письма на {to_email}: {e}")
            return False

    async def send_confirmation_code(self, to_email: str, code: str) -> bool:
        """Отправка одноразового кода подтверждения"""

        message = EmailMessage()
        message["From"] = f"Банковский сервис <{self.from_email}>"
        message["To"] = to_email
        message["Subject"] = "Код подтверждения пополнения счёта"

        # Шаблон письма
        body = f"""
        <html>
            <body>
                <h2>Подтверждение операции</h2>
                <p>Ваш одноразовый код для пополнения счёта:</p>
                <h1 style="color: #2e7d32; letter-spacing: 5px;">{code}</h1>
                <p>Код действителен в течение 10 минут.</p>
                <p><small>Если вы не запрашивали пополнение, просто проигнорируйте это письмо.</small></p>
            </body>
        </html>
        """
        message.add_alternative(body, subtype="html")

        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            # Для порта 465 use_tls=True
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=True,  # Для Mail.ru SSL (465)
                tls_context=ssl_context,
                timeout=10,
            )
            logger.info(f"[EmailService] Код успешно отправлен на {to_email}")
            return True

        except Exception as e:
            logger.error(f"[EmailService] Ошибка отправки письма на {to_email}: {e}")
            return False


email_service = EmailService()
