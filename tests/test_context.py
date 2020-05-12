import pytest

from valasp import Context


def test_max_arity_must_be_positive():
    with pytest.raises(ValueError):
        Context(0)
