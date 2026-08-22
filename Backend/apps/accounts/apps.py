from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # `name` is the import path; `label` is the short name used by
    # `makemigrations accounts`, FK strings ("accounts.Model") and AUTH_USER_MODEL.
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "Accounts"
