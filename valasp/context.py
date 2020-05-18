# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

import inspect
import warnings

import clingo
from types import FunctionType
from typing import ClassVar, List, Callable, Optional

from valasp.domain.name import PredicateName, ClassName
from valasp.domain.raisers import ValAspWarning


class Context:
    def __init__(self, max_arity: int = 16):
        if not (1 <= max_arity <= 99):
            raise ValueError("max_arity must be in 1..99, but received {max_arity}")

        self.__globals = {k: v for k, v in globals().items() if k[0:2] == '__' or k[0].islower()}
        self.__reserved = set(self.__globals.keys())
        self.__validators: List[str] = []
        self.__classes: List[ClassVar] = []

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
        key = str(ClassName(other.__name__))
        if self.is_reserved(key):
            raise KeyError(f'{key} is reserved')
        self.__globals[key] = other
        self.__reserved.add(key)
        self.__classes.append(other)

    def register_term(self, name: PredicateName, args: List[str], body_lines: List[str]):
        setattr(self, str(name), self.make_fun(str(name), args, body_lines))

    def is_reserved(self, key: str) -> bool:
        return key in self.__reserved

    def add_validator(self, predicate: PredicateName, arity: int, fun: Optional[str] = None) -> None:
        args_as_vars = ','.join(f'X{i}' for i in range(arity))
        at_term = f'valasp_validate_{predicate}'
        constraint = f':- {predicate}({args_as_vars}); '
        if fun is None:
            constraint += f'@{at_term}({args_as_vars}) != 1.'
        elif fun is '':
            constraint += f'@{at_term}(({args_as_vars},)) != 1.'
        else:
            constraint += f'@{at_term}({fun}({args_as_vars})) != 1.'
        self.__validators.append(constraint)
        self.register_term(PredicateName(at_term), ['value'], [
            f'{predicate.to_class()}(value)',
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

    def run_grounder(self, base_program: List[str]) -> clingo.Control:
        control = clingo.Control()
        control.add("base", [], '\n'.join(base_program + [self.validators()]))
        control.ground([("base", [])], context=self)
        return control

    def run_class_checks(self, prefix: str = 'check') -> None:
        for cls in self.__classes:
            for method in inspect.getmembers(cls, predicate=inspect.ismethod):
                if method[0].startswith(f'{prefix}'):
                    m = getattr(cls, method[0])
                    if len(inspect.signature(m).parameters) != 0:
                        warnings.warn(f"ignore method {m.__name__} of class {cls.__name__} because it has parameters",
                                      ValAspWarning)
                    else:
                        m()

    def run_solver(self, base_program: List[str]) -> List[clingo.SymbolicAtom]:
        control = self.run_grounder(base_program)
        self.run_class_checks()
        res = []

        def on_model(model):
            nonlocal res
            for atom in model.symbols(atoms=True):
                res.append(atom)

        control.solve(on_model=on_model)
        return res

    def run(self, control: clingo.Control, with_validators: bool = True, with_solve: bool = True) -> None:
        control.add("valasp", [], self.validators() if with_validators else '')
        if with_validators:
            self.run_class_checks('before_grounding')
        control.ground([("base", []), ("valasp", [])], context=self)
        if with_validators:
            self.run_class_checks('after_grounding')
        if with_solve:
            control.solve()
