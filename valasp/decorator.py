# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

"""This module define the decorator :meth:`validate` and the associated enum :class:`Fun`."""

import inspect
import warnings
from enum import Enum
from typing import ClassVar, List, Optional

from valasp.context import Context
from valasp.domain.name import ClassName
from valasp.domain.primitives import Type
from valasp.domain.raisers import ValAspWarning


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


def _decorate(cls: ClassVar, context: Context, is_predicate: bool, with_fun: Fun, auto_blacklist: bool):
    """Utility function to apply the :meth:`validate` decorator. Not intended to be used otherwise."""

    class_name = ClassName(cls.__name__)
    annotations = getattr(cls, '__annotations__', {})
    if not annotations:
        raise TypeError('cannot process classes with no annotations')
    args = list(f'{a}' for a in annotations)

    def process_with_fun() -> Optional[str]:
        nonlocal with_fun
        if with_fun == Fun.FORWARD_IMPLICIT:
            if len(annotations) == 1:
                with_fun = Fun.FORWARD
            else:
                with_fun = Fun.IMPLICIT
        if with_fun == Fun.IMPLICIT:
            return class_name.to_predicate().value
        if with_fun == Fun.FORWARD:
            if len(annotations) != 1:
                raise TypeError('FORWARD requires exactly one annotation')
            return None
        assert with_fun == Fun.TUPLE
        return ''

    def has_method(method: str) -> bool:
        return getattr(cls, method, None) != getattr(object, method, None)

    def set_method(method: str, arg_names: List[str], body_lines: List[str]) -> None:
        fun = context.make_fun(f'{class_name}.{method}', arg_names, body_lines, with_self=True)
        setattr(cls, method, fun)

    def add_init() -> None:
        if has_method('__init__'):
            raise ValueError("cannot process classes with __init__() constructor")

        def unpack(fun_name: str) -> List[str]:
            if with_fun_string is None:
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
            if Type.is_primitive(typ):
                return Type.get_primitive(typ).init_code(arg)
            return [f'self.{arg} = {typ.__name__}({arg})']

        body = unpack(with_fun_string)
        for k, v in annotations.items():
            body.extend(init_arg(k, v))

        for method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if method[0].startswith('check'):
                m = getattr(cls, method[0])
                if len(inspect.signature(m).parameters) != 1:
                    warnings.warn(f"ignore method {m.__name__} of class {cls.__name__} because it has parameters",
                                  ValAspWarning)
                else:
                    body.append(f'self.{m.__name__}()')

        if getattr(cls, '__post_init__', None):
            body.append('self.__post_init__()')

        set_method('__init__', ['value'], body)

    def add_str() -> None:
        if not has_method('__str__'):
            body = [f"return '{class_name}(' + " + " + ',' + ".join(f'str(self.{a})' for a in args) + " + ')'"]
            set_method('__str__', [], body)

    def add_cmp() -> None:
        self_tuple = "(" + ','.join(f'self.{a}' for a in args) + ")"
        other_tuple = "(" + ','.join(f'other.{a}' for a in args) + ")"
        methods = [('eq', '=='), ('ne', '!='), ('lt', '<'), ('le', '<='), ('ge', '>='), ('gt', '>')]
        for m in methods:
            if not has_method(f'__{m[0]}__'):
                set_method(f'__{m[0]}__', ['other'], [f"return {self_tuple} {m[1]} {other_tuple}"])

    with_fun_string = process_with_fun()
    add_init()
    add_str()
    add_cmp()
    if is_predicate:
        context.add_validator(class_name.to_predicate(), len(args), with_fun_string)
    if auto_blacklist:
        context.blacklist(class_name.to_predicate(), context.all_arities_but(len(args)))

    context.register_class(cls)


def validate(context: Context, is_predicate: bool = True, with_fun: Fun = Fun.FORWARD_IMPLICIT, auto_blacklist: bool = True):
    """Decorator to process classes for ASP validation.

    Annotations on a decorated class are used to define attributes and to inject an ``__init__()`` method.
    If the class defines a ``__post_init__()`` method, it is called at the end of the ``__init__()`` method.
    Other common magic methods are also injected, unless already defined in the class.

    :param context: the context where the class must be registered
    :param is_predicate: True if the class is associated with a predicate in the ASP program
    :param with_fun: modality of initialization for instances of the class
    :param auto_blacklist: if True, predicates with the same name but different arities are blacklisted
    :return: a decorator
    """
    def decorator(cls: ClassVar):
        _decorate(cls, context, is_predicate, with_fun, auto_blacklist)
        return cls
    return decorator
