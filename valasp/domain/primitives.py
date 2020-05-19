# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

from dataclasses import dataclass
from typing import List, ClassVar

import clingo
import typing


@dataclass(frozen=True)
class Type:
    __primitives = None

    def __init__(self):
        raise TypeError('this class must be used only as a marker')

    @staticmethod
    def _init_code(arg: str) -> List[str]:
        return [
            f'if not isinstance({arg}, clingo.Symbol):',
            f'    raise TypeError(f"expecting clingo.Symbol, but received type({{{arg}}})")',
        ]

    @classmethod
    def is_primitive(cls, typ: ClassVar) -> bool:
        return typ in cls.__primitives

    @classmethod
    def get_primitive(cls, typ: ClassVar) -> ClassVar:
        return cls.__primitives[typ]

    @classmethod
    def set_primitives(cls, value) -> None:
        if cls.__primitives:
            raise PermissionError(f'attempt to call set_primitives of {cls} from outside its module')
        cls.__primitives = value


@dataclass(frozen=True)
class Integer(Type):
    def __init__(self):
        super().__init__()

    @classmethod
    def init_code(cls, arg: str) -> List[str]:
        return super()._init_code(arg) + [
            f'if {arg}.type != clingo.SymbolType.Number:',
            f'    raise TypeError(f"expecting clingo.SymbolType.Number, but received {{{arg}}}")',
            f'self.{arg} = {arg}.number',
            f'if not({cls.min()} <= self.{arg} <= {cls.max()}):',
            f'    raise OverflowError(f"argument {arg} will overflow with value {{{arg}}}")',
        ]

    @classmethod
    def max(cls) -> int:
        return 2**31 - 1

    @classmethod
    def min(cls) -> int:
        return -2**31

    @classmethod
    def parse(cls, value: str) -> int:
        res = int(value)
        if not(cls.min() <= res <= cls.max()):
            raise OverflowError(f"{value} will overflow")
        return res


@dataclass(frozen=True)
class String(Type):
    def __init__(self):
        super().__init__()

    @classmethod
    def init_code(cls, arg: str) -> List[str]:
        return super()._init_code(arg) + [
            f'if {arg}.type != clingo.SymbolType.String:',
            f'    raise TypeError(f"expecting clingo.SymbolType.String, but received {{{arg}}}")',
            f'self.{arg} = {arg}.string',
        ]


@dataclass(frozen=True)
class Alpha(Type):
    def __init__(self):
        super().__init__()

    @classmethod
    def init_code(cls, arg: str) -> List[str]:
        return super()._init_code(arg) + [
            f'if {arg}.type != clingo.SymbolType.Function:',
            f'    raise TypeError(f"expecting clingo.SymbolType.Function, but received {{{arg}}}")',
            f'if {arg}.arguments:',
            f'    raise TypeError(f"expecting function of arity 0, but it is {{{arg}.arguments}}")',
            f'self.{arg} = {arg}.name',
        ]


@dataclass(frozen=True)
class Any(Type):
    def __init__(self):
        super().__init__()

    @classmethod
    def init_code(cls, arg: str) -> List[str]:
        return super()._init_code(arg) + [
            f'if {arg}.type == clingo.SymbolType.Number:',
            f'    self.{arg} = {arg}.number',
            f'elif {arg}.type == clingo.SymbolType.String:',
            f'    self.{arg} = {arg}.string',
            f'elif {arg}.type == clingo.SymbolType.Function:',
            f'    self.{arg} = {arg}',
            f'else:'
            f'    raise ValueError("expecting Number, String or Function, received {{{arg}.type}}")'
        ]


Type.set_primitives({
    Integer: Integer,
    int: Integer,
    clingo.Number: Integer,

    String: String,
    str: String,
    clingo.String: String,

    Alpha: Alpha,

    Any: Any,
    typing.Any: Any,
})
