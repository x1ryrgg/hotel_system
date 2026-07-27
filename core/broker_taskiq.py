__all__ = ("broker", 'scheduler')


from taskiq_aio_pika import AioPikaBroker
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from core.config import settings

broker = AioPikaBroker(
    url=settings.BROKER_URL
)

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)