import keyword

import pytest

from valasp.domain.names import ClassName, PredicateName, AttributeName


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


def test_underscore_prefix_in_class_name_to_predicate():
    assert str(ClassName('_Abc').to_predicate()) == '_abc'


def test_underscore_prefix_in_predicate_name_to_class():
    assert str(PredicateName('_abc').to_class()) == '_Abc'


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


def test_single_quotes_are_not_supported():
    for name in ["a'", "'a", "'a'", "_'_a'", "'''''a'''''"]:
        with pytest.raises(ValueError):
            PredicateName(name)
        with pytest.raises(ValueError):
            ClassName(name)


def test_attribute_name():
    for name in ["att", "aTt", "aaT", "aTT", "_aT", "__a_T", "a_"]:
        assert AttributeName(name).value == name
    for name in ["Att", "ATt", "AaT", "ATT", "_AT", "__A_T", "A_"]:
        with pytest.raises(ValueError):
            AttributeName(name)
    for name in keyword.kwlist:
        with pytest.raises(ValueError):
            AttributeName(name)
