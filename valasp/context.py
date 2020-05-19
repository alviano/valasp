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
    """The place where classes and @-terms can be registered to make them available for the ASP system.

    Typical usage just amount to create an instance and pass it to all applications of the ``validate`` decorator, and
    at the end call the method ``run()`` to execute the ASP system.
    """

    def __init__(self, max_arity: int = 16):
        """Create a context object.

        :param max_arity: the largest arity to be validated (16 is a reasonable upper bound)
        """
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
        """Return a function obtained by compiling the given code.

        The provided code can refer classes and @-terms registered in the context.

        :param name: the name of the function to create (for reference in errors)
        :param args: the argument names of the function
        :param body_lines: the actual code
        :param with_self: True if ``self`` must be included in the arguments
        :return: a function
        """
        args = ('self, ' if with_self else '') + ','.join(args)
        sig = f"def {name.replace('.', '__')}({args}):"
        body = '\n    '.join(body_lines)
        code = compile(f"{sig}\n    {body}", f"<def {name}({args})>", "exec")
        return FunctionType(code.co_consts[0], self.__globals)

    def register_class(self, other: ClassVar) -> None:
        """Add the given class to the context.

        :param other: a class
        :raise: KeyError if the name of the class is already used
        """
        key = str(ClassName(other.__name__))
        if self.is_reserved(key):
            raise KeyError(f'{key} is reserved')
        self.__globals[key] = other
        self.__reserved.add(key)
        self.__classes.append(other)

    def register_term(self, name: PredicateName, args: List[str], body_lines: List[str]) -> None:
        """Add the given @-term to the context.

        :param name: the name of the @-term
        :param args: the argument names
        :param body_lines: the code to be associated with the @-term
        """
        setattr(self, str(name), self.make_fun(str(name), args, body_lines))

    def is_reserved(self, key: str) -> bool:
        """Return True if the given key is reserved.

        :param key: a string
        :return: True if reserved
        """
        return key in self.__reserved

    def add_validator(self, predicate: PredicateName, arity: int, fun: Optional[str] = None) -> None:
        """Add a constraint validator for the given predicate name.

        The constraint validator is paired with an @-term, which in turn calls the constructor of the associated class name.

        :param predicate: a predicate name to be validated
        :param arity: the arity of the predicate
        :param fun: the function name expected by the constructor of the associated class name, or None if the constructor expects a single value
        """
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
        """Return a string with all constraint validators.

        :return: constraints in a string
        """
        return '\n'.join(self.__validators)

    def blacklist(self, predicate: PredicateName, arities: List[int] = None) -> None:
        """Add the given predicate name to the blacklist, for all provided arities.

        :param predicate: the predicate name to blacklist
        :param arities: a list of arities, or None for blacklisting all arities
        """
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
        """Return a list of all arities but ``excluded``.

        :param excluded: an arity to exclude
        :return: a list of arities
        """
        return [x+1 for x in range(self.__max_arity) if x+1 != excluded]

    def run_grounder(self, base_program: List[str]) -> clingo.Control:
        """Run grounder for the given ASP code, including all validators.

        :param base_program: ASP code
        :return: the resulting controller
        """
        control = clingo.Control()
        control.add("base", [], '\n'.join(base_program + [self.validators()]))
        control.ground([("base", [])], context=self)
        return control

    def run_class_methods(self, prefix: str = 'check') -> None:
        """Crawl all class methods with a given prefix, and a call them.

        :param prefix: a string
        """
        for cls in self.__classes:
            for method in inspect.getmembers(cls, predicate=inspect.ismethod):
                if method[0].startswith(f'{prefix}'):
                    m = getattr(cls, method[0])
                    if len(inspect.signature(m).parameters) != 0:
                        warnings.warn(f"ignore method {m.__name__} of class {cls.__name__} because it has parameters",
                                      ValAspWarning)
                    else:
                        m()

    def run_solver(self, base_program: List[str]) -> Optional[List[clingo.SymbolicAtom]]:
        """Run solver on the given ASP program, including all validators.

        :param base_program: ASP code
        :return: a model, or None if the program is inconsistent
        """
        control = self.run_grounder(base_program)
        self.run_class_methods()
        res = None

        def on_model(model):
            nonlocal res
            res = []
            for atom in model.symbols(atoms=True):
                res.append(atom)

        control.solve(on_model=on_model)
        return res

    def run(self, control: clingo.Control, on_model: Callable = None, aux_program: List[str] = None,
            with_validators: bool = True, with_solve: bool = True) -> None:
        """Run grounder on the given controller, possibly performing validation and searching for a model.

        :param control: a controller
        :param on_model: a callback function to process a model
        :param aux_program: more ASP code to add to the program
        :param with_validators: if True, validator constraints are added, and ``before_grounding*`` and ``after_grounding*`` class methods are called
        :param with_solve: if True, a model is searched
        """
        if with_validators:
            control.add("valasp", [], self.validators())
            self.run_class_methods('before_grounding')
        if aux_program:
            control.add("aux_program", [], '\n'.join(aux_program))
        control.ground([("base", []), ("valasp", []), ("aux_program", [])], context=self)
        if with_validators:
            self.run_class_methods('after_grounding')
        if with_solve:
            control.solve(on_model=on_model)
