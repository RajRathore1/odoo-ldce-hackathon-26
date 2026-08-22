from django.apps import AppConfig


class TripsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # `name` is the import path; `label` is the short name used by
    # `makemigrations trips`, FK strings ("trips.Model") and AUTH_USER_MODEL.
    name = "apps.trips"
    label = "trips"
    verbose_name = "Trips"
