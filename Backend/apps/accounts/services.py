"""
accounts — services. Owner: Dev A.

WRITE layer: transactions, cross-model orchestration, side effects.
Returns objects, never response bodies.
"""

import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import PasswordResetToken, User

logger = logging.getLogger(__name__)


def issue_tokens(user: User) -> dict[str, str]:
    """The `tokens` object in the register and login responses."""
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@transaction.atomic
def register_user(**validated) -> tuple[User, dict[str, str]]:
    """Create an account and hand back an immediately usable token pair."""
    password = validated.pop("password")
    user = User.objects.create_user(password=password, **validated)
    return user, issue_tokens(user)


def login_user(user: User) -> dict[str, str]:
    """
    `last_login` is updated by SimpleJWT's `UPDATE_LAST_LOGIN` setting when the
    token is minted, so there is nothing to do here beyond issuing tokens. Kept
    as a named service so the view reads the same as `register`.
    """
    return issue_tokens(user)


def logout_user(refresh_token: str) -> None:
    """
    Blacklist a refresh token.

    Deliberately silent on an invalid or already-blacklisted token: logout must
    be idempotent. A client retrying a logout, or sending one it already used,
    should not see an error — the desired end state (that token is dead) holds
    either way.
    """
    try:
        RefreshToken(refresh_token).blacklist()
    except TokenError:
        logger.info("Logout called with an invalid or already-blacklisted token.")


def blacklist_all_tokens(user: User) -> int:
    """
    Kill every outstanding refresh token for a user.

    Used when an account is deleted or its password is reset: leaving live
    refresh tokens behind would let an old session keep minting access tokens
    after the credentials changed.
    """
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    count = 0
    for token in OutstandingToken.objects.filter(user=user):
        _, created = BlacklistedToken.objects.get_or_create(token=token)
        count += int(created)
    return count


# ------------------------------------------------------------------- passwords


@transaction.atomic
def issue_password_reset_token(email: str) -> PasswordResetToken | None:
    """
    Create a reset token for `email`, if such an account exists.

    Returns `None` for an unknown address — the **view must respond 200
    regardless**, or the endpoint becomes an account-enumeration oracle.

    Issuing invalidates the user's outstanding tokens, so a forwarded older
    email cannot still be used.
    """
    user = User.objects.filter(email__iexact=email.strip().lower()).first()
    if user is None:
        return None

    PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(
        used_at=timezone.now()
    )

    ttl = timedelta(minutes=settings.PASSWORD_RESET_TOKEN_TTL_MINUTES)
    token = PasswordResetToken.objects.create(
        user=user,
        # token_urlsafe(32) is 43 chars — inside the 64-char column.
        token=secrets.token_urlsafe(32),
        expires_at=timezone.now() + ttl,
    )

    # No mail server in this project. dev.py uses the console email backend, so
    # this is how the token reaches whoever is testing.
    logger.info("Password reset token for %s: %s", user.email, token.token)
    return token


@transaction.atomic
def reset_password(token_value: str, new_password: str) -> User:
    """
    Consume a reset token and set the new password.

    Raises `ValidationError` when the token is unknown, expired or already
    spent — one message for all three, so the endpoint does not confirm that a
    token ever existed.
    """
    from rest_framework.exceptions import ValidationError

    invalid = ValidationError(
        {"token": "This reset link is invalid or has expired. Request a new one."}
    )

    # select_for_update so two concurrent resets cannot both spend one token.
    # A no-op on SQLite, which serialises writes anyway, but correct if this
    # ever moves to Postgres.
    reset = (
        PasswordResetToken.objects.select_for_update()
        .select_related("user")
        .filter(token=token_value)
        .first()
    )
    if reset is None or not reset.is_valid:
        raise invalid

    user = reset.user
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])

    reset.used_at = timezone.now()
    reset.save(update_fields=["used_at", "updated_at"])

    # The password changed, so every existing session must die.
    blacklist_all_tokens(user)
    return user


@transaction.atomic
def change_password(user: User, new_password: str) -> None:
    """
    Set a new password for a logged-in user and end their other sessions.

    The caller's *current* refresh token dies too, so the client has to log in
    again. That is the intended behaviour — it is also the only way to be sure a
    stolen token is gone.
    """
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    blacklist_all_tokens(user)


# --------------------------------------------------------------------- account


@transaction.atomic
def delete_account(user: User) -> None:
    """
    Soft-delete the account and end every session.

    Soft, not hard: `BaseModel.delete()` marks the row, so the user's trips stay
    intact for admin analytics and the account can be restored. The email stays
    occupied — `RegisterSerializer.validate_email` checks `all_objects` for
    exactly this reason.
    """
    blacklist_all_tokens(user)
    user.is_active = False
    user.save(update_fields=["is_active", "updated_at"])
    user.delete()  # soft


# ---------------------------------------------------------------------- admin


@transaction.atomic
def admin_update_user(user: User, **fields) -> User:
    """
    Moderate an account: activate, deactivate, promote, demote.

    Deactivating **kills the sessions too**. Without that, an account an admin
    has just suspended keeps working until its access token expires, which is
    the whole point of suspending it.
    """
    was_active = user.is_active
    for name, value in fields.items():
        setattr(user, name, value)
    user.save()

    if was_active and not user.is_active:
        blacklist_all_tokens(user)
        logger.info("Admin deactivated user %s; sessions revoked", user.pk)
    return user


@transaction.atomic
def admin_delete_user(user: User) -> None:
    """Soft-delete an account from the admin tree. Same path as self-service."""
    delete_account(user)
    logger.info("Admin soft-deleted user %s", user.pk)


@transaction.atomic
def admin_restore_user(user: User) -> User:
    """
    Undo a soft delete.

    Reactivates as well as undeleting: `delete_account` set `is_active=False`, so
    restoring without it would give back a row nobody can log in to.
    """
    user.restore()
    user.is_active = True
    user.save(update_fields=["is_active", "updated_at"])
    logger.info("Admin restored user %s", user.pk)
    return user
