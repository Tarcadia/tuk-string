# -*- coding: UTF-8 -*-

import string
import re

from contextlib import suppress

from .identifier import Identifier


class Digits(Identifier):

    CHARSET = string.digits
    PATTERN = r"[0-9]+"

    def __init__(self, value):
        try:
            self._int = int(self)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid digits to integer: Digits({self}) from {value}")

    @property
    def int(self):
        return self._int


class DigitsRange(Identifier):

    _PADDING_ZERO = r"0"
    _RANGE_CONNECT = r"-"
    _RANGE_START = r"range_start"
    _RANGE_END = r"range_end"
    _RANGE_PATTERN = rf"^(?P<{_RANGE_START}>{Digits.PATTERN}){_RANGE_CONNECT}(?P<{_RANGE_END}>{Digits.PATTERN})$"

    CHARSET = _RANGE_CONNECT + string.digits
    PATTERN = rf"{Digits.PATTERN}{_RANGE_CONNECT}{Digits.PATTERN}"

    def __init__(self, value):
        _range_match = re.match(self._RANGE_PATTERN, self)
        if not _range_match:
            raise ValueError(f"Invalid digits range: DigitsRange({self}) from {value}")
        _range_start = _range_match.group(self._RANGE_START)
        _range_end = _range_match.group(self._RANGE_END)
        self._start = int(_range_start)
        self._end = int(_range_end)
        self._range = range(self._start, self._end + 1)
        self._length = None

        if _range_start.startswith(self._PADDING_ZERO):
            if not len(_range_start) == len(_range_end):
                raise ValueError(f"Invalid digits range with padding zero: {value}")
            self._length = len(_range_end)

    def range(self):
        if self._length is None:
            return (
                rf"{_d}"
                for _d in self._range
            )
        else:
            return (
                rf"{_d:{self._PADDING_ZERO}{self._length}d}"
                for _d in self._range
            )

    def inrange(self, digits:Digits, raise_mismatch_error:bool=False):
        try:
            digits = Digits(digits)
        except ValueError:
            if not raise_mismatch_error:
                return False
            raise
        if self._length is None:
            return (digits.int >= self._start) and (digits.int <= self._end)
        elif len(digits) == self._length:
            return (digits.int >= self._start) and (digits.int <= self._end)
        elif raise_mismatch_error:
            raise ValueError(f"Invalid digits with or without padding zero: {digits}")
        else:
            return False


class DigitsList(Identifier):

    _LIST_SPLITTER = r","
    _LIST_ITEM_PATTERN = rf"({Digits.PATTERN})|({DigitsRange.PATTERN})"
    CHARSET = _LIST_SPLITTER + Digits.CHARSET + DigitsRange.CHARSET
    PATTERN = rf"({_LIST_ITEM_PATTERN})({_LIST_SPLITTER}\s*({_LIST_ITEM_PATTERN}))*"

    class _Item:

        def __init__(self, value:str):
            _item = None
            with suppress(ValueError):
                _item = Digits(value)
            with suppress(ValueError):
                _item = DigitsRange(value)
            if _item is None:
                raise ValueError(f"Invalid digits or digits range: {value}")
            self._item = _item

        def iteritem(self):
            if isinstance(self._item, DigitsRange):
                return self._item.range()
            else:
                return [self._item]

        def initem(self, digits:Digits, raise_mismatch_error:bool=False):
            try:
                digits = Digits(digits)
            except ValueError:
                if not raise_mismatch_error:
                    return False
                raise
            if isinstance(self._item, DigitsRange):
                return self._item.inrange(digits,raise_mismatch_error=raise_mismatch_error)
            else:
                return (self._item == digits)


    def __new__(cls, value):
        value = str(value).replace(" ", "")
        return super().__new__(cls, value)

    def __init__(self, value):
        try:
            _list_split = str.split(value, self._LIST_SPLITTER)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid digits list: {value}")
        self._list = [DigitsList._Item(_item.strip()) for _item in _list_split]
    
    def list(self):
        return (_i for _item in self._list for _i in _item.iteritem())

    def inlist(self, digits:Digits, raise_mismatch_error:bool=False):
        try:
            digits = Digits(digits)
        except ValueError:
            if not raise_mismatch_error:
                return False
            raise
        return any((_item.initem(digits) for _item in self._list))


