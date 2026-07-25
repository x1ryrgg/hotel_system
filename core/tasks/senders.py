from core.broker_taskiq import broker
from core.utils.mailing import email_service, EmailService



@broker.task
async def send_verification_code_email_task(to_email: str, code: str):
     return await email_service.send_confirmation_code(to_email=to_email, code=code)


@broker.task
async def send_text_email_task(to_email: str, text: str):
     return await email_service.send_text_email(to_email=to_email, text=text)