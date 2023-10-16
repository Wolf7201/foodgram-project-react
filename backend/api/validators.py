import webcolors
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def validate_color(value):
    try:
        webcolors.hex_to_rgb(value)
    except ValueError as e:
        raise serializers.ValidationError("Недопустимое значение цвета.") from e


def validate_email_format(value):
    try:
        validate_email(value)
    except ValidationError as e:
        raise serializers.ValidationError(
            "Недопустимый формат адреса электронной почты."
        ) from e
