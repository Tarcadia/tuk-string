# -*- coding: UTF-8 -*-

import string
import re


class Identifier(str):

    CHARSET = string.ascii_letters + string.digits + r"_"
    PATTERN = r"[a-zA-Z_][a-zA-Z0-9_]*"

    @classmethod
    def validate(cls, value:str) -> bool:
        _validate = True
        if cls.CHARSET is not None:
            _validate &= all(c in cls.CHARSET for c in value)
        if cls.PATTERN is not None:
            _validate &= re.match(rf"^{cls.PATTERN}$", value) is not None
        return _validate

    def __new__(cls, value):
        value = str(value)
        if not cls.validate(value):
            raise ValueError(f"Invalid identifier: {value}")
        return super().__new__(cls, value)


class IdentifierLower(Identifier):

    CHARSET = string.ascii_lowercase + string.digits + r"_"

    def __new__(cls, value):
        value = str(value).lower()
        return super().__new__(cls, value)


class IdentifierUpper(Identifier):

    CHARSET = string.ascii_uppercase + string.digits + r"_"

    def __new__(cls, value):
        value = str(value).upper()
        return super().__new__(cls, value)

