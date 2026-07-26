__all__ = ("broker", )


from taskiq_aio_pika import AioPikaBroker
from core.config import settings

broker = AioPikaBroker(
    url=settings.BROKER_URL
)