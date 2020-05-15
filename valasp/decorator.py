import inspect
from typing import ClassVar, Callable, List, Optional, Any

from valasp.context import Context, ClassName


class ValAsp:
    def __init__(self, cls: ClassVar, context: Context, auto_blacklist: bool):
        self.cls = cls
        self.context = context

        self.name = ClassName(cls.__name__)
        self.annotations = getattr(self.cls, '__annotations__', {})
        self.args = list(f'{a}' for a in self.annotations)

        if not self.annotations:
            raise TypeError('cannot process classes with no annotations')

        self.__add_init()
        self.__add_str()
        self.__add_cmp()
        self.__add_validator()
        if auto_blacklist:
            self.__add_blacklist()

        self.context.register_class(self.cls)

    def has_method(self, method: str) -> bool:
        return getattr(self.cls, method, None) != getattr(object, method, None)

    def __set_method(self, method: str, args: List[str], body_lines: List[str]) -> None:
        fun = self.context.make_fun(f'{self.name}.{method}', args, body_lines, with_self=True)
        setattr(self.cls, method, fun)

    def __add_init(self) -> None:
        if self.has_method('__init__'):
            raise ValueError("cannot process classes with __init__() constructor")

        types = {
            int: ('clingo.SymbolType.Number', '.number'),
            str: ('clingo.SymbolType.String', '.string'),
            Callable: ('clingo.SymbolType.Function', ''),
        }

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
        for k, v in self.annotations.items():
            body.extend(init_arg(k, v))
        if getattr(self.cls, '__post_init__', None):
            body.append('self.__post_init__()')
        self.__set_method('__init__', self.args, body)

    def __add_str(self) -> None:
        if not self.has_method('__str__'):
            body = [f"return '{self.name}(' + " + " + ',' + ".join(f'str(self.{a})' for a in self.args) + " + ')'"]
            self.__set_method('__str__', [], body)

    def __add_cmp(self) -> None:
        self_tuple = "(" + ','.join(f'self.{a}' for a in self.args) + ")"
        other_tuple = "(" + ','.join(f'other.{a}' for a in self.args) + ")"
        methods = [('eq', '=='), ('ne', '!='), ('lt', '<'), ('le', '<='), ('ge', '>='), ('gt', '>')]
        for m in methods:
            if not self.has_method(f'__{m[0]}__'):
                self.__set_method(f'__{m[0]}__', ['other'], [f"return {self_tuple} {m[1]} {other_tuple}"])

    def __add_validator(self) -> None:
        self.context.add_validator(self.name.to_predicate(), len(self.args))

    def __add_blacklist(self) -> None:
        self.context.blacklist(self.name.to_predicate(), self.context.all_arities_but(len(self.args)))


def validate(context: Context, auto_blacklist: bool = True):
    def decorator(cls: ClassVar):
        ValAsp(cls, context, auto_blacklist)
        return cls
    return decorator
