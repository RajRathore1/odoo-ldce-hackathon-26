from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # `name` is the import path; `label` is the short name used by
    # `makemigrations activities`, FK strings ("activities.Model") and AUTH_USER_MODEL.
    name = "apps.activities"
    label = "activities"
    verbose_name = "Activities"
