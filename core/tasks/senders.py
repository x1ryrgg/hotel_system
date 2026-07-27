from core import broker, scheduler
from core.utils.mailing import email_service, EmailService
from core.database import async_session_maker
from datetime import datetime
from sqlalchemy import select, update
from core.models import VerificationCode
from core.logging_system import logger


@broker.task
async def send_verification_code_email_task(to_email: str, code: str):
     return await email_service.send_confirmation_code(to_email=to_email, code=code)


@broker.task
async def send_text_email_task(to_email: str, text: str):
     return await email_service.send_text_email(to_email=to_email, text=text)


@broker.task(schedule=[{"cron": "*/1 * * * *"}])
async def deactivate_expired_codes():
    async with async_session_maker() as session:
        time_now = datetime.now()
        result  = await session.execute(update(VerificationCode).where(
               VerificationCode.expires_at < time_now,
               VerificationCode.is_active == True
          ).values(is_active=False)
          ) 
        await session.commit()
        logger.info(
            f"[deactivate_expired_codes] Деактивировано {result.rowcount} кодов. "
        )
        return True