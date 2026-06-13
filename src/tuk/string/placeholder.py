# -*- coding: UTF-8 -*-

import string
import re

from .identifier import Identifier


def Placeholder(icls, vcls):

    if not issubclass(icls, Identifier):
        raise TypeError("Placeholder can only be applied to subclasses of Identifier.")

    if not issubclass(vcls, Identifier):
        raise TypeError("Placeholder value can only be subclasses of Identifier.")

    _PREFIX = r"${"
    _SUFFIX = r"}"

    if icls.PATTERN is None:
        _IPATTERN = rf"[{re.escape(icls.CHARSET)}]+"
    else:
        _IPATTERN = icls.PATTERN

    if vcls.PATTERN is None:
        _VPATTERN = rf"[{re.escape(vcls.CHARSET)}]+"
    else:
        _VPATTERN = vcls.PATTERN



    class Placeholder(Identifier):

        CHARSET = _PREFIX + _SUFFIX + icls.CHARSET
        PATTERN = rf"{re.escape(_PREFIX)}{_IPATTERN}{re.escape(_SUFFIX)}"

        def __new__(cls, identifier:icls):
            _placeholder = rf"{_PREFIX}{identifier}{_SUFFIX}"
            return super().__new__(cls, _placeholder)

        def __init__(self, identifier:icls):
            self._placeholder_identifier = identifier
            self._placeholder_value = None

        def __repr__(self):
            return rf"{self}:={self.value}"

        def with_value(self, value:vcls):
            _placeholder = Placeholder(self.identifier)
            _placeholder.value = value
            return _placeholder

        @property
        def identifier(self) -> icls:
            return self._placeholder_identifier

        @property
        def value(self) -> vcls:
            return self._placeholder_value

        @value.setter
        def value(self, value:vcls):
            self._placeholder_value = value

        @classmethod
        def picker(cls, picker:str):
            return _Picker(picker)
        
        @classmethod
        def placer(cls, placeholders:list["Placeholder"]):
            return _Placer(placeholders)



    class _Picker:

        _PICKER_MAPPER_PREFIX = "placeholder_"

        def __init__(self, picker:str):
            _PLACEHOLDER = "__placeholder_picker_matched_placeholder__"
            _PLAINTEXT = "__placeholder_picker_matched_plaintext__"
            _patt = rf"(?P<{_PLACEHOLDER}>{Placeholder.PATTERN})|(?P<{_PLAINTEXT}>.)"
            _mapper = {}
            def _repl(match:re.Match) -> str:
                if (_placeholder := match.group(_PLACEHOLDER)):
                    _mapper_name = rf"{_Picker._PICKER_MAPPER_PREFIX}{len(_mapper)}"
                    _mapper[_mapper_name] = _placeholder.removeprefix(_PREFIX).removesuffix(_SUFFIX)
                    return rf"(?P<{_mapper_name}>{_VPATTERN})"
                elif (_plaintext := match.group(_PLAINTEXT)):
                    return re.escape(_plaintext)
                else:
                    return ""
            _rexp = re.sub(_patt, _repl, picker)
            self._picker = picker
            self._mapper = _mapper
            self._pattern = re.compile(rf"^{_rexp}$")

        def pick(self, target:str) -> None | list[Placeholder]:
            matches = self._pattern.match(target)
            if not matches:
                return None
            return [
                Placeholder(
                    icls(self._mapper[_mapper_name])
                ).with_value(
                    vcls(matches.group(_mapper_name))
                )
                for _mapper_name in self._mapper
            ]



    class _Placer:

        _PLACER_MAPPER = "__placeholder_placer_identifier__"

        def __init__(self, placeholders:list[Placeholder]):
            self._placeholders = placeholders
            self._mapper_match_first = {
                placeholder.identifier: placeholder.value
                for placeholder in reversed(self._placeholders)
            }
            self._mapper_match_last = {
                placeholder.identifier: placeholder.value
                for placeholder in self._placeholders
            }
            self._pattern = re.compile(rf"{re.escape(_PREFIX)}(?P<{_Placer._PLACER_MAPPER}>{_IPATTERN}){re.escape(_SUFFIX)}")

        def place(self, placer:str, keep_unknown:bool=False, match_last:bool=True) -> str:

            if match_last:
                _mapper = self._mapper_match_last
            else:
                _mapper = self._mapper_match_first

            def _repl(match:re.Match) -> str:
                _identifier = icls(match.group(_Placer._PLACER_MAPPER))
                if _identifier in _mapper:
                    return _mapper[_identifier]
                elif keep_unknown:
                    return Placeholder(match)
                else:
                    return ""

            return self._pattern.sub(_repl, placer)

        def allplace(self, placer:"_Placer", keep_unknown:bool=False, match_last:bool=True) -> "_Placer":

            if match_last:
                _mapper = self._mapper_match_last
            else:
                _mapper = self._mapper_match_first

            def _repl(match:re.Match) -> str:
                _identifier = icls(match.group(_Placer._PLACER_MAPPER))
                if _identifier in _mapper:
                    return _mapper[_identifier]
                elif keep_unknown:
                    return Placeholder(match)
                else:
                    return ""

            return _Placer(
                [
                    _placeholder.with_value(
                        self._pattern.sub(_repl, _placeholder.value)
                    )
                    for _placeholder in placer._placeholders
                ]
            )
        
        def updated(self, placer: "_Placer") -> "_Placer":
            _placer = self.allplace(placer)
            return _Placer(dict.fromkeys([*self._placeholders, *_placer._placeholders]))



    return Placeholder

