import webcolors

from django.core.exceptions import ValidationError


def validate_color(value):
    try:
        webcolors.hex_to_rgb(value)
    except ValueError as e:
        raise ValidationError(
            'Недопустимое значение цвета.',
            params={'value': value},
        ) from e
