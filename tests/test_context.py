import pytest
from clingo import Number, Symbol, Control

from valasp import Context
from valasp.context import ClassName, PredicateName


def test_class_name_upper_case():
    with pytest.raises(ValueError):
        ClassName('invalid')


def test_class_name_to_predicate():
    pred: PredicateName = ClassName('ValidClassName').to_predicate()
    assert str(pred) == 'validClassName'


def test_class_name_to_predicate_to_class():
    cls = ClassName('ValidClassName')
    assert cls.to_predicate().to_class() == cls


def test_predicate_name_lower_case():
    with pytest.raises(ValueError):
        PredicateName('Invalid')


def test_predicate_name_to_class():
    cls: ClassName = PredicateName('validPredicateName').to_class()
    assert str(cls) == 'ValidPredicateName'


def test_predicate_name_to_class_to_predicate():
    pred = PredicateName('validPredicateName')
    assert pred.to_class().to_predicate() == pred


def test_underscore_prefix_in_names():
    assert str(PredicateName('_abc')) == '_abc'

    with pytest.raises(ValueError):
        PredicateName('_Abc')

    assert str(ClassName('_Abc')) == '_Abc'

    with pytest.raises(ValueError):
        ClassName('_abc')

    with pytest.raises(ValueError):
        PredicateName('_')

    with pytest.raises(ValueError):
        ClassName('_')

    with pytest.raises(ValueError):
        PredicateName('__')

    with pytest.raises(ValueError):
        ClassName('__')


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


def test_run_class_checks():
    class Foo:
        def __init__(self, _: Symbol):
            Foo.instances += 1

        @classmethod
        def check_exactly_two_instances(cls):
            if Foo.instances != 2:
                raise ValueError("please, define exactly two instances")

        def check_foo(self):
            raise ValueError("this will not be classed automatically")
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
            pass

    context = Context()
    context.register_class(Foo)

    with pytest.raises(TypeError):
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
        context.run(Control(), with_validators=True, with_solve=True)
