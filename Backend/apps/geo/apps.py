from django.apps import AppConfig


class GeoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # `name` is the import path; `label` is the short name used by
    # `makemigrations geo`, FK strings ("geo.Model") and AUTH_USER_MODEL.
    name = "apps.geo"
    label = "geo"
    verbose_name = "Geography"
