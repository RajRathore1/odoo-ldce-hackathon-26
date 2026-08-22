from django.apps import AppConfig


class BudgetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # `name` is the import path; `label` is the short name used by
    # `makemigrations budget`, FK strings ("budget.Model") and AUTH_USER_MODEL.
    name = "apps.budget"
    label = "budget"
    verbose_name = "Budget"
