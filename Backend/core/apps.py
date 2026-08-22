from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def configure_sqlite(sender, connection, **kwargs):
    """
    Apply our SQLite PRAGMAs on every new connection.

    Why a signal and not `DATABASES["OPTIONS"]`: SQLite's `init_command` option
    only landed in Django 5.1, and `foreign_keys` is a *per-connection* pragma —
    it has to run again for every connection Django opens, including the ones
    pytest and `runserver`'s autoreloader make. A signal covers all of them.

    - `journal_mode=WAL` lets a reader and a writer work at the same time, which
      is what stops "database is locked" when the dev server and a shell overlap.
      This one is persistent on the file, so it is a no-op after the first run.
    - `foreign_keys=ON` makes SQLite actually enforce FK constraints. Django sets
      this itself, but we are explicit: silently unenforced FKs would let bad
      rows into the demo data.
    - `synchronous=NORMAL` is safe under WAL and noticeably faster.
    """
    if connection.vendor != "sqlite":
        return
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA synchronous=NORMAL;")


class CoreConfig(AppConfig):
    """
    `core` is in INSTALLED_APPS purely so this module gets imported at startup
    and the receiver above is connected. `core/models.py` holds abstract models
    only, so this app never generates a migration.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    label = "core"
