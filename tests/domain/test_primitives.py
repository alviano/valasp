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

