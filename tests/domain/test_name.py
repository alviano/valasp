import pytest

from valasp.domain.name import ClassName, PredicateName


def test_class_name_no_blank():
    with pytest.raises(ValueError):
        ClassName('')


def test_class_name_upper_case():
    with pytest.raises(ValueError):
        ClassName('invalid')


def test_class_name_to_predicate():
    pred: PredicateName = ClassName('ValidClassName').to_predicate()
    assert str(pred) == 'validClassName'


def test_class_name_to_predicate_to_class():
    cls = ClassName('ValidClassName')
    assert cls.to_predicate().to_class() == cls


def test_underscore_prefix_in_class_names():
    assert str(ClassName('_Abc')) == '_Abc'

    with pytest.raises(ValueError):
        ClassName('_abc')

    with pytest.raises(ValueError):
        ClassName('_')

    with pytest.raises(ValueError):
        ClassName('__')


def test_predicate_name_no_blank():
    with pytest.raises(ValueError):
        PredicateName('')


def test_predicate_name_lower_case():
    with pytest.raises(ValueError):
        PredicateName('Invalid')


def test_predicate_name_to_class():
    cls: ClassName = PredicateName('validPredicateName').to_class()
    assert str(cls) == 'ValidPredicateName'


def test_predicate_name_to_class_to_predicate():
    pred = PredicateName('validPredicateName')
    assert pred.to_class().to_predicate() == pred


def test_underscore_prefix_in_predicate_names():
    assert str(PredicateName('_abc')) == '_abc'

    with pytest.raises(ValueError):
        PredicateName('_Abc')

    with pytest.raises(ValueError):
        PredicateName('_')

    with pytest.raises(ValueError):
        PredicateName('__')
