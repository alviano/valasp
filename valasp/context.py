import re

from clingo import SymbolType
from types import FunctionType
from typing import ClassVar, List, Callable


class Context:
    def __init__(self, max_arity: int = 16):
        if not (1 <= max_arity <= 99):
            raise ValueError("max_arity must be in 1..99, but received {max_arity}")

        self.__globals = dict(globals())
        self.__reserved = set(globals().keys())
        self.__validators: List[str] = []

        self.__max_arity = max_arity

        self.register_term('vasp_error', ['msg', 'args'], [f'raise TypeError(f"{{msg}}" + f"; args={{args}}")'])
        self.__reserved.add('vasp_error')

    def make_fun(self, name: str, args: List[str], body_lines: List[str], with_self: bool = False) -> Callable:
        args = ('self, ' if with_self else '') + ','.join(args)
        sig = f"def {name.replace('.', '__')}({args}):"
        body = '\n    '.join(body_lines)
        code = compile(f"{sig}\n    {body}", f"<def {name}({args})>", "exec")
        return FunctionType(code.co_consts[0], self.__globals)

    def register_class(self, other: ClassVar) -> None:
        key = other.__name__
        if not re.fullmatch(r'(SymbolType|[a-z_][A-Za-z0-9_]*)', key):
            raise ValueError("cannot register this class")
        if self.is_reserved(key):
            raise KeyError(f'{key} is reserved')
        self.__globals[key] = other

    def register_term(self, name: str, args: List[str], body_lines: List[str]):
        setattr(self, name, self.make_fun(name, args, body_lines))

    def is_reserved(self, key) -> bool:
        return key in self.__reserved

    def add_validator(self, predicate: str, arity: int) -> None:
        args_as_vars = ','.join(f'X{i}' for i in range(arity))
        self.__validators.append(f':- {predicate}({args_as_vars}); @validate_{predicate}({args_as_vars}) != 1.')
        self.register_term(f'validate_{predicate}', [args_as_vars], [
            f'{predicate}({args_as_vars})',
            f'return 1'
        ])

    def validators(self) -> str:
        return '\n'.join(self.__validators)

    def blacklist(self, predicate: str, arities: List[int] = None) -> None:
        if not arities:
            arities = list(range(1, self.__max_arity + 1))
        for arity in arities:
            if not (1 <= arity <= self.__max_arity):
                raise ValueError(f"arities must be in 1..{self.__max_arity}")

            args_as_vars = ','.join(f'X{i}' for i in range(arity))
            self.__validators.append(
                f':- {predicate}({args_as_vars}); '
                f'@vasp_error("{predicate}/{arity} is blacklisted", ({args_as_vars},)) == 1.\n'
                f'{predicate}({args_as_vars}) :- {predicate}({args_as_vars}).'
            )

    def all_arities_but(self, excluded: int) -> List[int]:
        return [x+1 for x in range(self.__max_arity) if x+1 != excluded]
