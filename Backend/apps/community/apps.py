from django.apps import AppConfig


class CommunityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # `name` is the import path; `label` is the short name used by
    # `makemigrations community`, FK strings ("community.Model") and AUTH_USER_MODEL.
    name = "apps.community"
    label = "community"
    verbose_name = "Community"
