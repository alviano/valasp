# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

from dataclasses import dataclass
from typing import List

import clingo
import typing


@dataclass(frozen=True)
class Integer:
    def __init__(self):
        raise TypeError('this class must be used only as a marker')

    @staticmethod
    def init_code(arg: str) -> List[str]:
        return [
            f'if {arg}.type != clingo.SymbolType.Number:',
            f'    raise TypeError(f"expecting clingo.SymbolType.Number, but received {{{arg}}}")',
            f'self.{arg} = {arg}.number',
        ]


@dataclass(frozen=True)
class String:
    def __init__(self):
        raise TypeError('this class must be used only as a marker')

    @staticmethod
    def init_code(arg: str) -> List[str]:
        return [
            f'if {arg}.type != clingo.SymbolType.String:',
            f'    raise TypeError(f"expecting clingo.SymbolType.String, but received {{{arg}}}")',
            f'self.{arg} = {arg}.string',
        ]


@dataclass(frozen=True)
class Alpha:
    type = 'clingo.SymbolType.Function'
    value = ''

    def __init__(self):
        raise TypeError('this class must be used only as a marker')

    @staticmethod
    def init_code(arg: str) -> List[str]:
        return [
            f'if {arg}.type != clingo.SymbolType.Function:',
            f'    raise TypeError(f"expecting clingo.SymbolType.Function, but received {{{arg}}}")',
            f'if {arg}.arguments:',
            f'    raise TypeError(f"expecting function of arity 0, but it is {{{arg}.arguments}}")',
            f'self.{arg} = {arg}.name',
        ]


@dataclass(frozen=True)
class Any:
    def __init__(self):
        raise TypeError('this class must be used only as a marker')

    @staticmethod
    def init_code(arg: str) -> List[str]:
        return [
            f'if {arg}.type == clingo.SymbolType.Number:',
            f'    self.{arg} = {arg}.number',
            f'elif {arg}.type == clingo.SymbolType.String:',
            f'    self.{arg} = {arg}.string',
            f'elif {arg}.type == clingo.SymbolType.Function:',
            f'    self.{arg} = {arg}',
            f'else:'
            f'    raise ValueError("expecting Number, String or Function, received {{{arg}.type}}")'
        ]


primitive_types = {
    Integer: Integer,
    int: Integer,
    clingo.Number: Integer,

    String: String,
    str: String,
    clingo.String: String,

    Alpha: Alpha,

    Any: Any,
    typing.Any: Any,
}
