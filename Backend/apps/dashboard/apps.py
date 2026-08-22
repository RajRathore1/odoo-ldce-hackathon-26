from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # `name` is the import path; `label` is the short name used by
    # `makemigrations dashboard`, FK strings ("dashboard.Model") and AUTH_USER_MODEL.
    name = "apps.dashboard"
    label = "dashboard"
    verbose_name = "Dashboard"
