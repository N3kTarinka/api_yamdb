import re

from django.core.exceptions import ValidationError


def username_validator(value):
    unmatched = re.sub(r'^[\w.@+-]+\Z', '', value)
    if value == 'me':
        raise ValidationError('Имя пользователя "me" использовать нельзя!')
    elif value in unmatched:
        raise ValidationError(
            f'Имя пользователя не должно содержать {unmatched}'
        )
    return value
