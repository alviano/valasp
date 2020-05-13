import pytest
from clingo import Number

from tests.utils import run_clingo
from valasp import Context, validate


def test_must_have_annotations():
    context = Context()

    with pytest.raises(TypeError):
        @validate(context=context)
        class OK:
            pass


def test_define_str_and_cmp():
    context = Context()

    @validate(context=context)
    class Pair:
        first: int
        second: int

    p12 = Pair(Number(1), Number(2))
    assert str(p12) == 'Pair(1,2)'

    p13 = Pair(Number(1), Number(3))
    p12_ = Pair(Number(1), Number(2))
    assert p12 < p13
    assert p13 > p12
    assert p12 == p12_


def test_int():
    context = Context()

    @validate(context=context)
    class Node:
        value: int

    model = run_clingo(context, ["node(0)."])
    assert str(model) == '[node(0)]'

    with pytest.raises(RuntimeError):
        run_clingo(context, ["node(a)."])


def test_post_init():
    context = Context()

    @validate(context=context)
    class Node:
        value: int

        def __post_init__(self):
            if not(1 <= self.value <= 10):
                raise ValueError("must be in 1..10")

    model = run_clingo(context, ["node(10)."])
    assert str(model) == '[node(10)]'

    with pytest.raises(RuntimeError):
        run_clingo(context, ["node(0)."])

    with pytest.raises(RuntimeError):
        run_clingo(context, ["node(11)."])


def test_string():
    context = Context()

    @validate(context=context)
    class Name:
        value: str

    model = run_clingo(context, ['name("mario").'])
    assert str(model) == '[name("mario")]'

    with pytest.raises(RuntimeError):
        run_clingo(context, ["name(mario)."])

    with pytest.raises(RuntimeError):
        run_clingo(context, ["name(123)."])


def test_complex_type():
    context = Context()

    @validate(context=context)
    class Node:
        value: int

    @validate(context=context)
    class Edge:
        from_: Node
        to: Node

        def __post_init__(self):
            if not(self.from_ < self.to):
                raise ValueError("nodes must be ordered")

    model = run_clingo(context, ['node(1). node(2). edge(1,2).'])
    assert str(model) == '[node(1), node(2), edge(1,2)]'

    with pytest.raises(RuntimeError):
        run_clingo(context, ['node(1). node(2). edge(2,1).'])
