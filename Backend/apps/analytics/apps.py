from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # `name` is the import path; `label` is the short name used by
    # `makemigrations analytics`, FK strings ("analytics.Model") and AUTH_USER_MODEL.
    name = "apps.analytics"
    label = "analytics"
    verbose_name = "Analytics"
