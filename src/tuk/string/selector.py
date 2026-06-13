# -*- coding: UTF-8 -*-

import string
import re

from .identifier import Identifier, IdentifierLenient
from .digits import Digits, DigitsRange, DigitsList


class _Predicate(IdentifierLenient):
    CHARSET = ""
    PATTERN = None
    TARGET = None

    def predicate(self, value:str):
        return False


class _PredicateWildcard(_Predicate):
    CHAR_WILDCARD = "*"
    CHARSET = CHAR_WILDCARD
    PATTERN = re.escape(CHAR_WILDCARD)
    TARGET = rf"[{re.escape(IdentifierLenient.CHARSET_FOLLOW)}]*"

    def predicate(self, value:str):
        return re.match(rf"^{self.TARGET}$", value)


class _PredicateDigits(_Predicate):
    CHAR_DIGITS = "#"
    CHARSET = CHAR_DIGITS
    PATTERN = re.escape(CHAR_DIGITS)
    TARGET = Digits.PATTERN

    def predicate(self, value:str):
        return re.match(rf"^{self.TARGET}$", value)


class _PredicateDigitsList(_Predicate):
    DIGITSLIST_PREFIX = "["
    DIGITSLIST_SUFFIX = "]"
    CHARSET = DIGITSLIST_PREFIX + DIGITSLIST_SUFFIX + DigitsList.CHARSET
    PATTERN = rf"{re.escape(DIGITSLIST_PREFIX)}{DigitsList.PATTERN}{re.escape(DIGITSLIST_SUFFIX)}"
    TARGET = Digits.PATTERN

    def __init__(self, _):
        self._digitslist = DigitsList(self.removeprefix(self.DIGITSLIST_PREFIX).removesuffix(self.DIGITSLIST_SUFFIX))

    def predicate(self, value:str):
        return self._digitslist.inlist(value)


def Predicate(predicate:str) -> _Predicate:
    if re.match(rf"^{_PredicateWildcard.PATTERN}$", predicate):
        return _PredicateWildcard(predicate)
    if re.match(rf"^{_PredicateDigits.PATTERN}$", predicate):
        return _PredicateDigits(predicate)
    if re.match(rf"^{_PredicateDigitsList.PATTERN}$", predicate):
        return _PredicateDigitsList(predicate)


class Selector(IdentifierLenient):

    CHAR_NEGATIVE = "!"
    CHARSET_PREDICATE = "".join(set(CHAR_NEGATIVE + _PredicateWildcard.CHARSET + _PredicateDigits.CHARSET + _PredicateDigitsList.CHARSET))

    _PATTERN_NEGATIVE = re.escape(CHAR_NEGATIVE)
    _PATTERN_PREDICATE = rf"({_PredicateWildcard.PATTERN})|({_PredicateDigits.PATTERN})|({_PredicateDigitsList.PATTERN})"
    _PATTERN_PART_INITIAL = rf"({_PATTERN_PREDICATE})|[{re.escape(IdentifierLenient.CHARSET_INITIAL)}]"
    _PATTERN_PART_FOLLOW = rf"({_PATTERN_PREDICATE})|[{re.escape(IdentifierLenient.CHARSET_FOLLOW)}]"

    _MAPPER_PREFIX = "predicate_"
    
    CHARSET = IdentifierLenient.CHARSET + CHARSET_PREDICATE
    PATTERN = rf"({_PATTERN_NEGATIVE}?)({_PATTERN_PART_INITIAL})({_PATTERN_PART_FOLLOW})*"

    def __new__(cls, value):
        value = str(value).replace(" ", "")
        return super().__new__(cls, value)

    def __init__(self, _):
        self._negative = self.startswith(Selector.CHAR_NEGATIVE)
        _PREDICATE = "__selector_matched_predicate__"
        _PLAINTEXT = "__selector_matched_plaintext__"
        _patt = rf"(?P<{_PREDICATE}>{Selector._PATTERN_PREDICATE})|(?P<{_PLAINTEXT}>.)"
        _mapper = {}
        def _repl(match:re.Match) -> str:
            if (_predicate := match.group(_PREDICATE)):
                _predicate = Predicate(_predicate)
                _mapper_name = rf"{Selector._MAPPER_PREFIX}{len(_mapper)}"
                _mapper[_mapper_name] = _predicate
                return rf"(?P<{_mapper_name}>{_predicate.TARGET})"
            elif (_plaintext := match.group(_PLAINTEXT)):
                return re.escape(_plaintext)
            else:
                return ""
        _rexp = re.sub(_patt, _repl, self.removeprefix(Selector.CHAR_NEGATIVE))
        self._mapper = _mapper
        self._pattern = re.compile(rf"^{_rexp}$")

    def select(self, initial:list[IdentifierLenient], universal:list[IdentifierLenient]):
        if self._negative:
            return [
                _i
                for _i in initial
                if not (_m := self._pattern.match(_i))
                or (
                    _m and not all(
                        _predicate.predicate(_m.group(_mapper_name))
                        for _mapper_name, _predicate in self._mapper.items()
                    )
                )
            ]
        else:
            return initial + [
                _i
                for _i in universal
                if not _i in initial
                if (_m := self._pattern.match(_i))
            ]

