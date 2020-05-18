# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

import inspect
import warnings
from enum import Enum
from typing import ClassVar, List, Optional

from valasp.context import Context
from valasp.domain.name import ClassName
from valasp.domain.primitives import primitive_types
from valasp.domain.raisers import ValAspWarning


class Fun(Enum):
    FORWARD_IMPLICIT = 0
    FORWARD = 1
    IMPLICIT = 2
    TUPLE = 3


class ValAsp:
    def __init__(self, cls: ClassVar, context: Context, is_predicate: bool, with_fun: Fun, auto_blacklist: bool):
        self.cls = cls
        self.context = context

        self.name = ClassName(cls.__name__)
        self.annotations = getattr(self.cls, '__annotations__', {})
        if not self.annotations:
            raise TypeError('cannot process classes with no annotations')

        self.with_fun = self.__with_fun(with_fun)

        args = list(f'{a}' for a in self.annotations)
        self.__add_init(args)
        self.__add_str(args)
        self.__add_cmp(args)
        if is_predicate:
            self.__add_validator(args)
        if auto_blacklist:
            self.__add_blacklist(args)

        self.context.register_class(self.cls)

    def __with_fun(self, with_fun) -> Optional[str]:
        if with_fun == Fun.FORWARD_IMPLICIT:
            if len(self.annotations) == 1:
                with_fun = Fun.FORWARD
            else:
                with_fun = Fun.IMPLICIT
        if with_fun == Fun.IMPLICIT:
            return self.name.to_predicate().value
        if with_fun == Fun.FORWARD:
            if len(self.annotations) != 1:
                raise TypeError('FORWARD requires exactly one annotation')
            return None
        if with_fun == Fun.TUPLE:
            return ''
        raise ValueError('unexpected value for with_fun:', with_fun)

    def has_method(self, method: str) -> bool:
        return getattr(self.cls, method, None) != getattr(object, method, None)

    def __set_method(self, method: str, args: List[str], body_lines: List[str]) -> None:
        fun = self.context.make_fun(f'{self.name}.{method}', args, body_lines, with_self=True)
        setattr(self.cls, method, fun)

    def __add_init(self, args: List[str]) -> None:
        if self.has_method('__init__'):
            raise ValueError("cannot process classes with __init__() constructor")

        def unpack(fun_name: str) -> List[str]:
            if self.with_fun is None:
                return [f'{args[0]} = value']
            return [
                f'if value.type != clingo.SymbolType.Function:',
                f'    raise TypeError(f"expecting clingo.SymbolType.Function, but received {{value.type}}")',
                f'if value.name != "{fun_name}":',
                f'    raise ValueError(f"expecting function \\"{fun_name}\\", but found \\"{{value.name}}\\"")',
                f'if len(value.arguments) != {len(args)}:',
                f'    raise ValueError(f"expecting arity {len(args)} for {fun_name}, '
                + f'but found {{len(value.arguments)}}")',
                f'{", ".join(args)}, = value.arguments',
            ]

        def init_arg(arg: str, typ: ClassName) -> List[str]:
            if typ in primitive_types:
                return primitive_types[typ].init_code(arg)
            return [f'self.{arg} = {typ.__name__}({arg})']

        body = unpack(self.with_fun)
        for k, v in self.annotations.items():
            body.extend(init_arg(k, v))

        for method in inspect.getmembers(self.cls, predicate=inspect.isfunction):
            if method[0].startswith('check'):
                m = getattr(self.cls, method[0])
                if len(inspect.signature(m).parameters) != 1:
                    warnings.warn(f"ignore method {m.__name__} of class {self.cls.__name__} because it has parameters",
                                  ValAspWarning)
                else:
                    body.append(f'self.{m.__name__}()')

        if getattr(self.cls, '__post_init__', None):
            body.append('self.__post_init__()')

        self.__set_method('__init__', ['value'], body)

    def __add_str(self, args: List[str]) -> None:
        if not self.has_method('__str__'):
            body = [f"return '{self.name}(' + " + " + ',' + ".join(f'str(self.{a})' for a in args) + " + ')'"]
            self.__set_method('__str__', [], body)

    def __add_cmp(self, args: List[str]) -> None:
        self_tuple = "(" + ','.join(f'self.{a}' for a in args) + ")"
        other_tuple = "(" + ','.join(f'other.{a}' for a in args) + ")"
        methods = [('eq', '=='), ('ne', '!='), ('lt', '<'), ('le', '<='), ('ge', '>='), ('gt', '>')]
        for m in methods:
            if not self.has_method(f'__{m[0]}__'):
                self.__set_method(f'__{m[0]}__', ['other'], [f"return {self_tuple} {m[1]} {other_tuple}"])

    def __add_validator(self, args: List[str]) -> None:
        self.context.add_validator(self.name.to_predicate(), len(args), self.with_fun)

    def __add_blacklist(self, args: List[str]) -> None:
        self.context.blacklist(self.name.to_predicate(), self.context.all_arities_but(len(args)))


def validate(context: Context, is_predicate: bool = True, with_fun: Fun = Fun.FORWARD_IMPLICIT, auto_blacklist: bool = True):
    def decorator(cls: ClassVar):
        ValAsp(cls, context, is_predicate, with_fun, auto_blacklist)
        return cls
    return decorator
