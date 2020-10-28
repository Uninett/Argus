from django.core.validators import RegexValidator, _lazy_re_compile
from django.core.exceptions import ValidationError


__all__ = [
    "validate_lowercase",
    "validate_key",
    "validate_key_value",
]


def validate_lowercase(value: str):
    if not value.islower():
        raise ValidationError(f"'{value}' is not a lowercase string")


key_re = _lazy_re_compile(r"^[a-z0-9_]+\Z")
key_validator = RegexValidator(
    key_re,
    message="Enter a valid key consisting of lowercase letters, numbers and underscores.",
    code="invalid",
)


def validate_key(value):
    return key_validator(value)


key_value_re = _lazy_re_compile(r"^[a-z0-9_]+=.+?\Z")
key_value_validator = RegexValidator(
    key_value_re,
    message='Enter a valid key-value construct: "key=value", where key and value are strings.',
    code="invalid",
)


def validate_key_value(value):
    return key_value_validator(value)
