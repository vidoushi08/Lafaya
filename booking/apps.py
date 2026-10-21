from django.apps import AppConfig


class BookingConfig(AppConfig):
    name = 'booking'

    def ready(self):
        from .signals import connect_request_signals

        connect_request_signals()
