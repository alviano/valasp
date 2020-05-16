import pytest
from clingo import Number, Symbol, Control

from valasp.context import Context
from valasp.domain.name import PredicateName
from valasp.domain.raisers import ValAspWarning


def test_max_arity_must_be_positive():
    with pytest.raises(ValueError):
        Context(0)


def test_clingo_is_reserved():
    assert Context().is_reserved('clingo')


def test_make_fun_successor():
    context = Context()
    successor = context.make_fun('successor', ['x'], ['return x + 1'])
    assert successor(0) == 1
    assert successor(99) == 100


def test_make_fun_can_access_symbol_type():
    context = Context()
    is_number = context.make_fun('is_number', ['x'], ['return x.type == clingo.SymbolType.Number'])
    assert is_number(Number(1))


def test_register_class():
    class Sum:
        def __init__(self):
            self.value = 0

        def add(self, x: int) -> None:
            self.value += x

    context = Context()
    context.register_class(Sum)
    sum_first = context.make_fun('sum_first', ['n'], [
        'res = Sum()',
        'for i in range(n):',
        '    res.add(i)',
        'return res.value'
    ])
    assert sum_first(10) == sum(range(10))


def test_register_class_with_reserved_name():
    class A:
        a: int

    context = Context()
    context.register_class(A)
    with pytest.raises(KeyError):
        context.register_class(A)

    with pytest.raises(ValueError):
        class clingo:
            a: int

        context.register_class(clingo)


def test_run_solver():
    context = Context()
    assert str(context.run_solver(["hello_world."])) == "[hello_world]"


def test_register_term():
    context = Context()
    context.register_term(PredicateName('successor'), ['x'], ['return x.number + 1'])
    model = context.run_solver(["one(@successor(0))."])
    assert str(model) == '[one(1)]'


def test_add_validator():
    class PositiveNumber:
        def __init__(self, value: Symbol):
            if not(1 <= value.number):
                raise ValueError("not a positive number")
            self.value = value

    context = Context()
    context.register_class(PositiveNumber)
    context.add_validator(PredicateName('positiveNumber'), 1)
    model = context.run_solver(["positiveNumber(1)."])
    assert str(model) == '[positiveNumber(1)]'

    with pytest.raises(RuntimeError):
        context.run_solver(["positiveNumber(0)."])


def test_blacklist():
    context = Context()
    context.blacklist(PredicateName('number'), [2])

    model = context.run_solver(["number(1)."])
    assert str(model) == "[number(1)]"

    with pytest.raises(RuntimeError):
        context.run_solver(["number(1,2)."])


def test_blacklist_all_arities():
    context = Context()
    context.blacklist(PredicateName('number'))
    with pytest.raises(RuntimeError):
        context.run_solver(["number(1)."])


def test_cannot_blacklist_arity_zero():
    with pytest.raises(ValueError):
        Context().blacklist(PredicateName('foo'), [0])


def test_run_class_checks():
    class Foo:
        def __init__(self, _: Symbol):
            Foo.instances += 1
            self.check_foo()

        @classmethod
        def check_exactly_two_instances(cls):
            if Foo.instances != 2:
                raise ValueError("please, define exactly two instances")

        def check_foo(self):
            pass
    Foo.instances = 0

    context = Context()
    context.register_class(Foo)
    context.add_validator(PredicateName('foo'), 1)

    with pytest.raises(ValueError):
        Foo(Number(1))
        context.run_class_checks()

    Foo(Number(2))
    context.run_class_checks()

    with pytest.raises(ValueError):
        Foo(Number(3))
        context.run_class_checks()


def test_class_checks_must_have_no_arguments():
    class Foo:
        @classmethod
        def check_fail(cls, _):
            raise TypeError()

    context = Context()
    context.register_class(Foo)

    with pytest.raises(TypeError):
        Foo.check_fail(0)

    with pytest.warns(ValAspWarning):
        context.run_class_checks()


def test_run():
    context = Context()

    class Foo:
        @classmethod
        def check_fail(cls):
            raise ValueError('so nice')

    context.register_class(Foo)

    context.run(Control(), with_validators=False)
    context.run(Control(), with_validators=False, with_solve=False)

    with pytest.raises(ValueError):
        context.run(Control(), with_validators=True)

    with pytest.raises(ValueError):
        context.run(Control(), with_validators=True, with_solve=True)
