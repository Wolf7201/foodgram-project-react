import re
import webcolors

from django.core.exceptions import ValidationError


def validate_username(value):
    if value == 'me':
        raise ValidationError(
            'Имя пользователя не может быть "me"',
            params={'value': value},
        )
    if re.search(r'^[a-zA-Z][a-zA-Z0-9-_.]{1,20}$', value) is None:
        raise ValidationError(
            'Не допустимые символы в имени',
            params={'value': value},
        )


def validate_color(value):
    try:
        webcolors.hex_to_rgb(value)
    except ValueError as e:
        raise ValidationError(
            'Недопустимое значение цвета.',
            params={'value': value},
        ) from e
