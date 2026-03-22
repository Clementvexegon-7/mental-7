# ================================================================
#  mentalapp/apps.py
# ================================================================

from django.apps import AppConfig


class MentalappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'mentalapp'
    verbose_name       = 'MindWell Mental Health App'

    def ready(self):
        # Import signals to ensure they are registered on startup
        import mentalapp.models  # noqa: F401