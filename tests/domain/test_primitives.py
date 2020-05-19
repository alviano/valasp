import pytest

from valasp.domain.primitives import Type, Integer, String, Alpha, Any


def test_type_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Type()


def test_integer_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Integer()


def test_string_cannot_be_instantiated():
    with pytest.raises(TypeError):
        String()


def test_alpha_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Alpha()


def test_any_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Any()


def test_set_primitives_is_not_accessible():
    with pytest.raises(PermissionError):
        Type.set_primitives({})


def test_integer_validate():
    assert Integer.parse('0') == 0
    assert Integer.parse('1') == 1
    assert Integer.parse('-1') == -1
    assert Integer.parse(str(Integer.max())) == Integer.max()
    assert Integer.parse(str(Integer.min())) == Integer.min()
    with pytest.raises(ValueError):
        Integer.parse('a')
    with pytest.raises(OverflowError):
        Integer.parse(str(Integer.max() + 1))
    with pytest.raises(OverflowError):
        Integer.parse(str(Integer.min() - 1))
