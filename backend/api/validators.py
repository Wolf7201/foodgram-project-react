import webcolors
from rest_framework import serializers


def validate_color(value):
    try:
        webcolors.hex_to_rgb(value)
    except ValueError as e:
        raise serializers.ValidationError(
            "Недопустимое значение цвета."
        ) from e
