from django.apps import AppConfig

class HubConfig(AppConfig):
    """Configuration for the Hub application. Necessary for Django to recognize the app and its components. Registers signals."""
    name = 'hub'

    def ready(self):
        import hub.signals
