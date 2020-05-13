import pytest
from clingo import Number, Symbol

from tests.utils import run_clingo
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


def test_register_term():
    context = Context()
    context.register_term(PredicateName('successor'), ['x'], ['return x.number + 1'])
    model = run_clingo(context, ["one(@successor(0))."])
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
    model = run_clingo(context, ["positiveNumber(1)."])
    assert str(model) == '[positiveNumber(1)]'

    with pytest.raises(RuntimeError):
        run_clingo(context, ["positiveNumber(0)."])


def test_blacklist():
    context = Context()
    context.blacklist(PredicateName('number'), [2])

    model = run_clingo(context, ["number(1)."])
    assert str(model) == "[number(1)]"

    with pytest.raises(RuntimeError):
        run_clingo(context, ["number(1,2)."])
