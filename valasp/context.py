import re
from dataclasses import dataclass

import clingo
from types import FunctionType
from typing import ClassVar, List, Callable


@dataclass(frozen=True)
class ClassName:
    value: str

    def __post_init__(self):
        if not(1 <= len(self.value) <= 256):
            raise ValueError("the length of the given value is not in the range 1..256")
        if not re.fullmatch(r'[A-Z_][A-Za-z0-9_]*', self.value):
            raise ValueError("invalid value")

    def __str__(self):
        return self.value

    def to_predicate(self) -> 'PredicateName':
        return PredicateName(self.value[0].lower() + self.value[1:])


@dataclass(frozen=True)
class PredicateName:
    value: str

    def __post_init__(self):
        if not(1 <= len(self.value) <= 256):
            raise ValueError("the length of the given value is not in the range 1..256")
        if not re.fullmatch(r'[a-z_][A-Za-z0-9_]*', self.value):
            raise ValueError("invalid value")

    def __str__(self):
        return self.value

    def to_class(self) -> ClassName:
        return ClassName(self.value[0].upper() + self.value[1:])


class Context:
    def __init__(self, max_arity: int = 16):
        if not (1 <= max_arity <= 99):
            raise ValueError("max_arity must be in 1..99, but received {max_arity}")

        self.__globals = {k: v for k, v in globals().items() if k[0:2] == '__' or k[0].islower()}
        self.__reserved = set(self.__globals.keys())
        self.__validators: List[str] = []

        self.__max_arity = max_arity

        self.register_term(PredicateName('valasp_error'), ['msg', 'args'], [
            f'raise TypeError(f"{{msg}}" + f"; args={{args}}")'])
        self.__reserved.add('valasp_error')

    def make_fun(self, name: str, args: List[str], body_lines: List[str], with_self: bool = False) -> Callable:
        args = ('self, ' if with_self else '') + ','.join(args)
        sig = f"def {name.replace('.', '__')}({args}):"
        body = '\n    '.join(body_lines)
        code = compile(f"{sig}\n    {body}", f"<def {name}({args})>", "exec")
        return FunctionType(code.co_consts[0], self.__globals)

    def register_class(self, other: ClassVar) -> None:
        key = ClassName(other.__name__)
        if self.is_reserved(str(key)):
            raise KeyError(f'{key} is reserved')
        self.__globals[str(key)] = other

    def register_term(self, name: PredicateName, args: List[str], body_lines: List[str]):
        setattr(self, str(name), self.make_fun(str(name), args, body_lines))

    def is_reserved(self, key: str) -> bool:
        return key in self.__reserved

    def add_validator(self, predicate: PredicateName, arity: int) -> None:
        args_as_vars = ','.join(f'X{i}' for i in range(arity))
        self.__validators.append(f':- {predicate}({args_as_vars}); @validate_{predicate}({args_as_vars}) != 1.')
        self.register_term(PredicateName(f'validate_{predicate}'), [args_as_vars], [
            f'{predicate.to_class()}({args_as_vars})',
            f'return 1'
        ])

    def validators(self) -> str:
        return '\n'.join(self.__validators)

    def blacklist(self, predicate: PredicateName, arities: List[int] = None) -> None:
        if not arities:
            arities = list(range(1, self.__max_arity + 1))
        for arity in arities:
            if not (1 <= arity <= self.__max_arity):
                raise ValueError(f"arities must be in 1..{self.__max_arity}")

            args_as_vars = ','.join(f'X{i}' for i in range(arity))
            self.__validators.append(
                f':- {predicate}({args_as_vars}); '
                f'@valasp_error("{predicate}/{arity} is blacklisted", ({args_as_vars},)) == 1.\n'
                f'{predicate}({args_as_vars}) :- {predicate}({args_as_vars}).'
            )

    def all_arities_but(self, excluded: int) -> List[int]:
        return [x+1 for x in range(self.__max_arity) if x+1 != excluded]

    @classmethod
    def __ensure_clingo_is_imported(cls):
        clingo.SymbolType.Number(0)
