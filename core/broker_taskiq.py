from taskiq_aio_pika import AioPikaBroker
from core.config import settings

broker = AioPikaBroker(
    url=settings.BROKER_URL,
    task_modules=["core.tasks.senders"]
)