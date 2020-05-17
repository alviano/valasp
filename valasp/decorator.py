# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

import inspect
import warnings
from enum import Enum
from typing import ClassVar, Callable, List, Any

from valasp.context import Context
from valasp.domain.name import ClassName
from valasp.domain.raisers import ValAspWarning


class Use(Enum):
    Predicate = 0
    Value = 1
    Function = 2
    Tuple = 3


class ValAsp:
    def __init__(self, cls: ClassVar, context: Context, use_as: Use, auto_blacklist: bool):
        self.cls = cls
        self.context = context

        self.name = ClassName(cls.__name__)
        self.annotations = getattr(self.cls, '__annotations__', {})

        if not self.annotations:
            raise TypeError('cannot process classes with no annotations')
        if use_as == Use.Value and len(self.annotations) != 1:
            raise TypeError(f'Use.Value needs arity 1, not {len(self.annotations)}')

        args = list(f'{a}' for a in self.annotations)
        self.__add_init(use_as, args)
        self.__add_str(args)
        self.__add_cmp(args)
        if use_as == Use.Predicate:
            self.__add_validator(args)
        if auto_blacklist:
            self.__add_blacklist(args)

        self.context.register_class(self.cls)

    def has_method(self, method: str) -> bool:
        return getattr(self.cls, method, None) != getattr(object, method, None)

    def __set_method(self, method: str, args: List[str], body_lines: List[str]) -> None:
        fun = self.context.make_fun(f'{self.name}.{method}', args, body_lines, with_self=True)
        setattr(self.cls, method, fun)

    def __add_init(self, use_as: Use, args: List[str]) -> None:
        if self.has_method('__init__'):
            raise ValueError("cannot process classes with __init__() constructor")

        types = {
            int: ('clingo.SymbolType.Number', '.number'),
            str: ('clingo.SymbolType.String', '.string'),
            Callable: ('clingo.SymbolType.Function', ''),
        }

        def unpack(fun_name: str) -> List[str]:
            return [
                f'if fun.type != clingo.SymbolType.Function:',
                f'    raise TypeError(f"expecting clingo.SymbolType.Function, but received {{fun.type}}")',
                f'if fun.name != "{fun_name}":',
                f'    raise ValueError(f"expecting function \\"{fun_name}\\", but found \\"{{fun.name}}\\"")',
                f'if len(fun.arguments) != {len(args)}:',
                f'    raise ValueError(f"expecting arity {len(args)} for {fun_name}, '
                + f'but found {{len(fun.arguments)}}")',
                f'{", ".join(args)}, = fun.arguments',
            ]

        def init_arg(arg: str, typ) -> List[str]:
            if typ in types:
                typ, extract = types[typ]
                return [
                    f'if {arg}.type != {typ}:',
                    f'    raise TypeError(f"expecting {typ}, but received {{{arg}}}")',
                    f'self.{arg} = {arg}{extract}',
                ]
            if typ == Any:
                return [
                    f'if {arg}.type == clingo.SymbolType.Number:',
                    f'    self.{arg} = {arg}.number',
                    f'elif {arg}.type == clingo.SymbolType.String:',
                    f'    self.{arg} = {arg}.string',
                    f'elif {arg}.type == clingo.SymbolType.Function:',
                    f'    self.{arg} = {arg}',
                    f'else:'
                    f'    raise ValueError("expecting Number, String or Function, received {typ}")'
                ]
            return [f'self.{arg} = {typ.__name__}({arg})']

        body = []
        if use_as == Use.Function:
            body += unpack(self.name.to_predicate().value)
        elif use_as == Use.Tuple:
            body += unpack('')
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

        if use_as in [Use.Function, Use.Tuple]:
            self.__set_method('__init__', ['fun'], body)
        else:
            self.__set_method('__init__', args, body)

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
        self.context.add_validator(self.name.to_predicate(), len(args))

    def __add_blacklist(self, args: List[str]) -> None:
        self.context.blacklist(self.name.to_predicate(), self.context.all_arities_but(len(args)))


def validate(context: Context, use_as: Use = Use.Predicate, auto_blacklist: bool = True):
    def decorator(cls: ClassVar):
        ValAsp(cls, context, use_as, auto_blacklist)
        return cls
    return decorator
