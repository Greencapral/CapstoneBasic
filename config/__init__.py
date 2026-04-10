__all__ ={
    "is_docker_container",
    "celery_app",
}

from config.is_docker_container import is_docker_container
from config.celery import app as celery_app