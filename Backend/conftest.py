"""
pytest configuration shared by every test module.

Only global test-environment tweaks belong here. Fixtures that are specific to
one app go in that app's `tests/`.
"""


def pytest_configure():
    from django.conf import settings

    # PBKDF2 does ~600k iterations per hash by design. Every factory-built user
    # pays that twice (create + set_password), which dominated the runtime of
    # the suite. MD5 is obviously not acceptable anywhere near production — it
    # is set here only, and only because a test hash never leaves the process.
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

    # Never let a test touch a real mailbox, whatever dev.py says.
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
