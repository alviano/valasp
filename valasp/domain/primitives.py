# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

from dataclasses import dataclass
from typing import List, ClassVar

import clingo
import typing

from valasp.domain.name import PredicateName


@dataclass(frozen=True)
class Type:
    """Base class for type annotations.

    This class cannot be instantiated, and its subclasses are expected to satisfy this invariant.
    """
    __primitives = None

    def __init__(self):
        raise TypeError('this class must be used only as a marker')

    @staticmethod
    def init_code(arg: str) -> List[str]:
        """Return code to validate the type of the given argument name.

        Subclasses are expected to call this method in their init_code() method.

        :param arg: the name of the argument
        :return: validation code
        """
        return [
            f'if not isinstance({arg}, clingo.Symbol):',
            f'    raise TypeError(f"expecting clingo.Symbol, but received type({{{arg}}})")',
        ]

    @classmethod
    def is_primitive(cls, typ: ClassVar) -> bool:
        """Return true if typ is considered a primitive type.

        :param typ: a type
        :return: true if typ is a primitive type
        """
        return typ in cls.__primitives

    @classmethod
    def get_primitive(cls, typ: ClassVar) -> 'Type':
        """Return a subclass of Type associated with typ.

        :param typ: a type for which Type.is_primitive(typ) == True
        :raise: KeyError if Type.is_primitive(typ) != True
        :return: a subclass of Type associated with typ
        """
        return cls.__primitives[typ]

    @classmethod
    def set_primitives(cls, value) -> None:
        """Init the Type class with primitive types.

        This method is called at the end of this file, and cannot be called a second time.

        :param value: a dictionary (see the bottom of this file)
        :raise: PermissionError if called a second time
        """
        if cls.__primitives:
            raise PermissionError(f'attempt to call set_primitives of {cls} from outside its module')
        cls.__primitives = value


@dataclass(frozen=True)
class Integer(Type):
    """Primitive type representing integers.

    This class cannot be instantiated.
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def init_code(cls, arg: str) -> List[str]:
        return super().init_code(arg) + [
            f'if {arg}.type != clingo.SymbolType.Number:',
            f'    raise TypeError(f"expecting clingo.SymbolType.Number, but received {{{arg}}}")',
            f'self.{arg} = {arg}.number',
            f'if not({cls.min()} <= self.{arg} <= {cls.max()}):',
            f'    raise OverflowError(f"argument {arg} will overflow with value {{{arg}}}")',
        ]

    @classmethod
    def max(cls) -> int:
        """Return the greatest integer for the ASP system.

        :return: the greatest integer
        """
        return 2**31 - 1

    @classmethod
    def min(cls) -> int:
        """Return the smallest integer for the ASP system.

        :return: the smallest integer
        """
        return -2**31

    @classmethod
    def parse(cls, value: str) -> int:
        """Return the integer represented in value.

        :param value: a string to be parsed
        :raise: TypeError if value is not an integer
        :raise: OverflowError if value does not fit into a 32-bit signed integer
        :return: the integer in value
        """
        res = int(value)
        if not(cls.min() <= res <= cls.max()):
            raise OverflowError(f"{value} will overflow")
        return res


@dataclass(frozen=True)
class String(Type):
    """
    Primitive type representing strings.

    This class cannot be instantiated.
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def init_code(cls, arg: str) -> List[str]:
        return super().init_code(arg) + [
            f'if {arg}.type != clingo.SymbolType.String:',
            f'    raise TypeError(f"expecting clingo.SymbolType.String, but received {{{arg}}}")',
            f'self.{arg} = {arg}.string',
        ]


@dataclass(frozen=True)
class Alpha(Type):
    """Primitive type representing named constants.

    This class cannot be instantiated.
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def init_code(cls, arg: str) -> List[str]:
        return super().init_code(arg) + [
            f'if {arg}.type != clingo.SymbolType.Function:',
            f'    raise TypeError(f"expecting clingo.SymbolType.Function, but received {{{arg}}}")',
            f'if {arg}.arguments:',
            f'    raise TypeError(f"expecting function of arity 0, but it is {{{arg}.arguments}}")',
            f'self.{arg} = {arg}.name',
        ]

    @classmethod
    def parse(cls, value: str) -> str:
        """Return value, as any string is valid

        :param value: a string to be parsed
        :return: value
        """
        return value


@dataclass(frozen=True)
class Any(Type):
    """Primitive type representing wildcards.

        This class cannot be instantiated.
        """

    def __init__(self):
        super().__init__()

    @classmethod
    def init_code(cls, arg: str) -> List[str]:
        return super().init_code(arg) + [
            f'if {arg}.type == clingo.SymbolType.Number:',
            f'    self.{arg} = {arg}.number',
            f'elif {arg}.type == clingo.SymbolType.String:',
            f'    self.{arg} = {arg}.string',
            f'elif {arg}.type == clingo.SymbolType.Function:',
            f'    self.{arg} = {arg}',
            f'else:'
            f'    raise ValueError("expecting Number, String or Function, received {{{arg}.type}}")'
        ]

    @classmethod
    def parse(cls, value: str) -> str:
        """Return value, or raise an exception if value is not valid

        :param value: a string to be parsed
        :raise: ValueError if value is not a valid function name
        :return: value
        """
        return PredicateName(value).value


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
