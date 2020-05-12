from typing import ClassVar, Callable, List

from valasp.context import Context


class ValAsp:
    def __init__(self, cls: ClassVar, context: Context):
        self.cls = cls
        self.context = context

        self.name = cls.__name__
        self.annotations = getattr(self.cls, '__annotations__', {})
        self.args = list(f'{a}' for a in self.annotations)

        if not self.annotations:
            raise ValueError('cannot process classes with no annotations')

        self.__add_init()
        self.__add_str()
        self.__add_cmp()
        self.__add_validator()

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
            int: ('SymbolType.Number', '.number'),
            str: ('SymbolType.String', '.string'),
            Callable: ('SymbolType.Function', ''),
        }

        def init_arg(arg: str, typ) -> List[str]:
            if typ in types:
                typ, extract = types[typ]
                return [
                    f'if {arg}.type != {typ}:',
                    f'    raise TypeError(f"expecting {typ}, but received {{{arg}}}")',
                    f'self.{arg} = {arg}{extract}',
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
        self.context.add_validator(self.name, len(self.args))
        self.context.blacklist(self.name, self.context.all_arities_but(len(self.args)))


def validate(context: Context):
    def decorator(cls: ClassVar):
        ValAsp(cls, context)
        return cls
    return decorator
