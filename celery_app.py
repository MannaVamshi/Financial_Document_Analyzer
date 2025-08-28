from celery import Celery

celery = Celery(
    "worker",
    broker="memory://",
    backend="rpc://"
)
