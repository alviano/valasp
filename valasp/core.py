# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

"""This module defines the :class:`Context` class, a convenient place where classes and @-terms are registered.

An instance of :class:`Context` can wrap one or more classes and functions to be used as @-terms by an ASP system.
Classes can be registered by using a convenient decorator, and are used to inject data validation into an external ASP program.
"""

import inspect as valasp_inspect
import warnings as valasp_warnings

import clingo
from types import FunctionType
from typing import ClassVar, List, Callable, Optional, Any

from valasp.domain.names import PredicateName, ClassName
from valasp.domain.primitive_types import Type, Fun
from valasp.domain.raisers import ValAspWarning


class Context:
    """The place where classes and @-terms can be registered to make them available for the ASP system.

    Typical usage just amount to create an instance and apply the ``valasp`` decorator to one or more classes, and
    at the end call the method ``run()`` to execute the ASP system.
    """

    def __init__(self, wrap: List[Any] = None, max_arity: int = 16):
        """Create a context object.

        If you have already a context object defining methods for @-terms used by your program, you can pass it in the wrap list.
        Similarly, if your @-terms are implemented by global functions, you can pass them in the wrap list.

        :param wrap: a list of objects and functions defining @-terms
        :param max_arity: the largest arity to be validated (16 is a reasonable upper bound)
        """
        if not (1 <= max_arity <= 99):
            raise ValueError("max_arity must be in 1..99, but received {max_arity}")

        self.__wrap = list(wrap) if wrap else []

        self.__globals = {k: v for k, v in globals().items() if k[0:2] == '__' or k[0].islower()}
        self.__reserved = set(self.__globals.keys())
        self.__validators: List[str] = []
        self.__classes: List[ClassVar] = []

        self.__max_arity = max_arity

        self.__secret = object()

    def __getattr__(self, name):
        def method(*args):
            for wrap in self.__wrap:
                if isinstance(wrap,Callable) and wrap.__name__ == name:
                    return wrap(*args)
                m = getattr(wrap, name, None)
                if m:
                    return m(*args)
            if name in self.__globals:
                return self.__globals[name](*args)
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'; wrong @-term?")

        return method

    def valasp(self, is_predicate: bool = True, with_fun: Fun = Fun.FORWARD_IMPLICIT, auto_blacklist: bool = True):
        """Decorator to process classes for ASP validation.

        Annotations on a decorated class are used to define attributes and to inject an ``__init__()`` method.
        If the class defines a ``__post_init__()`` method, it is called at the end of the ``__init__()`` method.
        Other common magic methods are also injected, unless already defined in the class.

        :param is_predicate: True if the class is associated with a predicate in the ASP program
        :param with_fun: modality of initialization for instances of the class
        :param auto_blacklist: if True, predicates with the same name but different arities are blacklisted
        :return: a decorator
        """

        def decorator(cls: ClassVar):
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
                if method == '__init__':
                    filename = f'constructor of {class_name.to_predicate()}'
                else:
                    filename = f'method {method} of {class_name.to_predicate()}'
                fun = self.valasp_make_fun(filename, f'{class_name}.{method}', arg_names, body_lines, with_self=True)
                setattr(cls, method, fun)

            def add_init() -> None:
                if has_method('__init__'):
                    raise ValueError("cannot process classes with __init__() constructor")

                def unpack(fun_name: str) -> List[str]:
                    if with_fun_string is None:
                        return [f'{args[0]} = value']
                    return [
                        f'if value.type != clingo.SymbolType.Function:',
                        f'    raise TypeError(f"expecting clingo.SymbolType.Function, but received {{value.type}}; invalid term {{value}}")',
                        f'if value.name != "{fun_name}":',
                        f'    raise ValueError(f"expecting function \\"{fun_name}\\", but found \\"{{value.name}}\\"; invalid term {{value}}")',
                        f'if len(value.arguments) != {len(args)}:',
                        f'    raise ValueError(f"expecting arity {len(args)} for {fun_name if fun_name else "TUPLE"}, but found {{len(value.arguments)}}; invalid term {{value}}")',
                        f'{", ".join(args)}, = value.arguments',
                    ]

                def init_arg(arg: str, typ: ClassName) -> List[str]:
                    if Type.is_primitive(typ):
                        return Type.get_primitive(typ).init_code(arg)
                    return [f'self.{arg} = {typ.__name__}({arg})']

                body = unpack(with_fun_string)
                for k, v in annotations.items():
                    body.extend(init_arg(k, v))

                for method in valasp_inspect.getmembers(cls, predicate=valasp_inspect.isfunction):
                    if method[0].startswith('check'):
                        m = getattr(cls, method[0])
                        if len(valasp_inspect.signature(m).parameters) != 1:
                            valasp_warnings.warn(
                                f"ignore method {m.__name__} of class {cls.__name__} because it has parameters",
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
                self.valasp_add_validator(class_name.to_predicate(), len(args), with_fun_string)
            if auto_blacklist:
                self.valasp_blacklist(class_name.to_predicate(), self.valasp_all_arities_but(len(args)))

            self.valasp_register_class(cls)
            return cls
        return decorator


    def valasp_error(self, msg, args):
        raise TypeError(f"{msg}; args={args}")

    @staticmethod
    def valasp_extract_error_message(error: Exception) -> str:
        res = []
        lines = str(error).split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('File "<valasp|'):
                line = line.split('|')[1]
                if not res:
                    res.append(line)
                else:
                    res.append(f'    in {line.strip()}')
            elif 'Error:' in line:
                line = line.split(':')[1]
                res.append(f'  with error: {line.strip()}')

        return '\n'.join(res)

    def valasp_make_fun(self, filename: str, name: str, args: List[str], body_lines: List[str], with_self: bool = False) -> Callable:
        """Return a function obtained by compiling the given code.

        The provided code can refer classes and @-terms registered in the context.

        :param filename: the name of the file associated with the given code (for reference in errors)
        :param name: the name of the function to create (for reference in errors)
        :param args: the argument names of the function
        :param body_lines: the actual code
        :param with_self: True if ``self`` must be included in the arguments
        :return: a function
        """
        args = ('self, ' if with_self else '') + ','.join(args)
        sig = f"def {name.replace('.', '__')}({args}):"
        body = '\n    '.join(body_lines)
        code = compile(f"{sig}\n    {body}", f"<valasp|{filename}|>", "exec")
        return FunctionType(code.co_consts[0], self.__globals)

    def valasp_register_class(self, other: ClassVar) -> None:
        """Add the given class to the context.

        :param other: a class
        :raise: KeyError if the name of the class is reserved
        """
        key = str(ClassName(other.__name__))
        if self.valasp_is_reserved(key):
            raise KeyError(f'{key} is reserved')
        self.__globals[key] = other
        self.__reserved.add(key)
        self.__classes.append(other)

    def valasp_register_term(self, filename: str, name: PredicateName, args: List[str], body_lines: List[str], auth: Any = None) -> None:
        """Add the given @-term to the context.

        :param filename: the name of the file associated with the given code (for reference in errors)
        :param name: the name of the @-term
        :param args: the argument names
        :param auth: if it is the internal secret, the ``valasp`` prefix is authorized
        :param body_lines: the code to be associated with the @-term
        """
        if self.valasp_is_reserved(name.value, auth):
            raise KeyError(f'{name.value} is reserved')
        setattr(self, name.value, self.valasp_make_fun(filename, str(name), args, body_lines))

    def valasp_is_reserved(self, key: str, auth: Any = None) -> bool:
        """Return True if the given key is reserved.

        :param key: a string
        :param auth: if it is the internal secret, the ``valasp`` prefix is authorized
        :return: True if reserved
        """
        return (key in self.__reserved) or (auth != self.__secret and key.lower().startswith('valasp'))

    def valasp_add_validator(self, predicate: PredicateName, arity: int, fun: Optional[str] = None) -> None:
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
        self.valasp_register_term(f'Invalid instance of {predicate}:', PredicateName(at_term), ['value'], [
            f'try:'
            f'    {predicate.to_class()}(value)',
            f'except Exception as e:',
            f'    raise ValueError(f"{{e}} in atom {{value}}").with_traceback(e.__traceback__.tb_next) from None',
            f'return 1'
        ], auth=self.__secret)

    def valasp_validators(self) -> str:
        """Return a string with all constraint validators.

        :return: constraints in a string
        """
        return '\n'.join(self.__validators)

    def valasp_blacklist(self, predicate: PredicateName, arities: List[int] = None) -> None:
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

    def valasp_all_arities_but(self, excluded: int) -> List[int]:
        """Return a list of all arities but ``excluded``.

        :param excluded: an arity to exclude
        :return: a list of arities
        """
        return [x+1 for x in range(self.__max_arity) if x+1 != excluded]

    def valasp_run_grounder(self, base_program: List[str]) -> clingo.Control:
        """Run grounder for the given ASP code, including all validators.

        :param base_program: ASP code
        :return: the resulting controller
        """
        control = clingo.Control()
        control.add("base", [], '\n'.join(base_program + [self.valasp_validators()]))
        control.ground([("base", [])], context=self)
        return control

    def valasp_run_class_methods(self, prefix: str = 'check') -> None:
        """Crawl all class methods with a given prefix, and a call them.

        :param prefix: a string
        """
        for cls in self.__classes:
            for method in valasp_inspect.getmembers(cls, predicate=valasp_inspect.ismethod):
                if method[0].startswith(f'{prefix}'):
                    m = getattr(cls, method[0])
                    if len(valasp_inspect.signature(m).parameters) != 0:
                        valasp_warnings.warn(f"ignore method {m.__name__} of class {cls.__name__} because it has parameters",
                                      ValAspWarning)
                    else:
                        m()

    def valasp_run_solver(self, base_program: List[str]) -> Optional[List[clingo.SymbolicAtom]]:
        """Run solver on the given ASP program, including all validators.

        :param base_program: ASP code
        :return: a model, or None if the program is inconsistent
        """
        control = self.valasp_run_grounder(base_program)
        self.valasp_run_class_methods()
        res = None

        def on_model(model):
            nonlocal res
            res = []
            for atom in model.symbols(atoms=True):
                res.append(atom)

        # noinspection PyUnresolvedReferences
        control.solve(on_model=on_model)
        return res

    def valasp_run(self, control: clingo.Control, on_validation_done: Callable = None, on_model: Callable = None,
                   aux_program: List[str] = None, with_validators: bool = True, with_solve: bool = True) -> None:
        """Run grounder on the given controller, possibly performing validation and searching for a model.

        :param control: a controller
        :param on_validation_done: a function invoked after grounding, if no validation error is reported
        :param on_model: a callback function to process a model
        :param aux_program: more ASP code to add to the program
        :param with_validators: if True, validator constraints are added, and ``before_grounding*`` and ``after_grounding*`` class methods are called
        :param with_solve: if True, a model is searched
        """
        if with_validators:
            control.add("valasp", [], self.valasp_validators())
            self.valasp_run_class_methods('before_grounding')
        if aux_program:
            control.add("aux_program", [], '\n'.join(aux_program))
        control.ground([("base", []), ("valasp", []), ("aux_program", [])], context=self)
        if with_validators:
            self.valasp_run_class_methods('after_grounding')
        if on_validation_done:
            on_validation_done()
        if with_solve:
            # noinspection PyUnresolvedReferences
            control.solve(on_model=on_model)
