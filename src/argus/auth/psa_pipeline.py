"""
Place to put changes to the python social auth (psa) pipeline system.

See https://python-social-auth.readthedocs.io/en/latest/pipeline.html
for tons of detail that doesn't really help that much.
"""


def user_details(strategy, details, backend, user=None, *args, **kwargs):
    """Replaces social_core.pipeline.user.user_details in SOCIAL_AUTH_PIPELINE

    Only necessary to use if the scope-list didn't start out with "email" in it.
    When "email" has been added to the scope-list, this will set email on the
    user on next login. After all users have logged in again, the default
    authentication-pipeline can be restored.

    Also needed if we will always trust the email from the OIDC provider no
    matter what.

    The only change ``from social_core.pipeline.user.user_details`` is the
    commenting out of "email" in the ``protected``-tuple.
    """

    if not user:
        return

    changed = False

    if strategy.setting("NO_DEFAULT_PROTECTED_USER_FIELDS") is True:
        protected = ()
    else:
        protected = (
            "username",
            "id",
            "pk",
            "password",  # 'email',
            "is_active",
            "is_staff",
            "is_superuser",
        )

    protected = protected + tuple(strategy.setting("PROTECTED_USER_FIELDS", []))

    # Update user model attributes with the new data sent by the current
    # provider. Update on some attributes is disabled by default, for
    # example username and id fields. It's also possible to disable update
    # on fields defined in SOCIAL_AUTH_PROTECTED_USER_FIELDS.
    field_mapping = strategy.setting("USER_FIELD_MAPPING", {}, backend)
    for name, value in details.items():
        # Convert to existing user field if mapping exists
        name = field_mapping.get(name, name)
        if value is None or not hasattr(user, name) or name in protected:
            continue

        current_value = getattr(user, name, None)
        if current_value == value:
            continue

        changed = True
        setattr(user, name, value)

    if changed:
        strategy.storage.user.changed(user)
