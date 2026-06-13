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



    class Placeholder(icls):

        CHARSET = _PREFIX + _SUFFIX + icls.CHARSET
        PATTERN = rf"{re.escape(_PREFIX)}{_IPATTERN}{re.escape(_SUFFIX)}"

        def __new__(cls, value):
            return super().__new__(cls, value)

        @classmethod
        def picker(cls, picker:str):
            return _Picker(picker)



    class _Picker:

        _PICKER_MAPPER_PREFIX = "placeholder_"

        def __init__(self, picker:str):
            _picker_split = re.split(fr"({Placeholder.PATTERN})", picker)
            _rexp = r""
            _mapper = {}
            _mapper_idx = 0
            for _part in _picker_split:
                if re.match(Placeholder.PATTERN, _part):
                    _mapper_name = rf"{_Picker._PICKER_MAPPER_PREFIX}{_mapper_idx}"
                    _mapper[_mapper_name] = _part.removeprefix(_PREFIX).removesuffix(_SUFFIX)
                    _mapper_idx += 1
                    _rexp += fr"(?P<{_mapper_name}>{_VPATTERN})"
                else:
                    _rexp += re.escape(_part)
            self._mapper = _mapper
            self._pattern = re.compile(rf"^{_rexp}$")

        def pick(self, target:str) -> None | dict[icls, vcls]:
            matches = self._pattern.match(target)
            if not matches:
                return None
            return {
                icls(self._mapper[_mapper_name])
                : vcls(matches.group(_mapper_name))
                for _mapper_name in self._mapper
            }



    return Placeholder

