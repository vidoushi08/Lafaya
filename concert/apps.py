from django.apps import AppConfig


class ConcertConfig(AppConfig):
    name = "concert"

    def ready(self):
        from . import signals
