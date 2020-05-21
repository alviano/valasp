# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

"""The enum :class:`Fun` and the primitive types are defined in this module.

The primitive types are markers to be used in annotations. They cannot be instantiated, and offer a very limited set of utility function.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, ClassVar

import clingo
import typing

from valasp.domain.names import PredicateName


class Fun(Enum):
    """Modalities for the :meth:`validate` decorator.

    * **FORWARD_IMPLICIT** means FORWARD for symbols of arity 1, and IMPLICIT otherwise.
    * **FORWARD** can be used with symbols of arity 1 and essentially means to leave the init argument as it is.
    * **IMPLICIT** must be used if the init argument is expected to be a function with the same name of the symbol.
      The arguments of the function are unpacked.
    * **TUPLE** is like IMPLICIT, but the function is expected to have emtpy name.
    """
    FORWARD_IMPLICIT = 0
    FORWARD = 1
    IMPLICIT = 2
    TUPLE = 3


@dataclass(frozen=True)
class Type:
    """Base class for type annotations.

    This class cannot be instantiated, and its subclasses are expected to satisfy this invariant.
    """
    __primitives = None

    def __init__(self):
        raise NotImplemented('this class must be used only as a marker')

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

    @classmethod
    def parse(cls, value: str) -> str:
        """Return value, or raises an exception if value is not a string.

        :param value: a string to be parsed
        :raise: TypeError if value is not str
        :return: value
        """
        if not isinstance(value, str):
            raise TypeError(f"expecting str, but found {type(value)}")
        return value


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
        :raise: TypeError if value is not an integer, or if its type is not str
        :raise: OverflowError if value does not fit into a 32-bit signed integer
        :return: the integer in value
        """
        res = int(super().parse(value))
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

    @classmethod
    def parse(cls, value: str) -> str:
        """Return value, as any string is valid

        :param value: a string to be parsed
        :return: value
        """
        return super().parse(value)


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
        """Return value, or raise an exception if value is not valid

        :param value: a string to be parsed
        :raise: ValueError if value is not a valid function name, or TypeError if the type of value is not str
        :return: value
        """
        value = super().parse(value)
        return PredicateName(value).value


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
