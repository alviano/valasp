from typing import Any

import pytest
from clingo import Number, String, Function

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

    model = context.run_solver(["node(0)."])
    assert str(model) == '[node(0)]'

    with pytest.raises(RuntimeError):
        context.run_solver(["node(a)."])


def test_post_init():
    context = Context()

    @validate(context=context)
    class Node:
        value: int

        def __post_init__(self):
            if not(1 <= self.value <= 10):
                raise ValueError("must be in 1..10")

    model = context.run_solver(["node(10)."])
    assert str(model) == '[node(10)]'

    with pytest.raises(RuntimeError):
        context.run_solver(["node(0)."])

    with pytest.raises(RuntimeError):
        context.run_solver(["node(11)."])


def test_string():
    context = Context()

    @validate(context=context)
    class Name:
        value: str

    model = context.run_solver(['name("mario").'])
    assert str(model) == '[name("mario")]'

    with pytest.raises(RuntimeError):
        context.run_solver(["name(mario)."])

    with pytest.raises(RuntimeError):
        context.run_solver(["name(123)."])


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

    model = context.run_solver(['node(1). node(2). edge(1,2).'])
    assert str(model) == '[node(1), node(2), edge(1,2)]'

    with pytest.raises(RuntimeError):
        context.run_solver(['node(1). node(2). edge(2,1).'])


def test_underscore_in_annotations():
    context = Context()

    @validate(context=context)
    class Foo:
        __init__: int

    assert str(Foo(Number(1))) == 'Foo(1)'
    assert Foo(Number(1)).__init__ == 1

    @validate(context=context)
    class Bar:
        __str__: int

    assert str(Bar(Number(1))) == 'Bar(1)'
    assert Bar(Number(1)).__str__ == 1


def test_auto_blacklist():
    context = Context()

    @validate(context=context)
    class Edge:
        source: int
        dest: int

    assert str(context.run_solver(["edge(1,2)."])) == '[edge(1,2)]'

    with pytest.raises(RuntimeError):
        context.run_solver(["edge(1,2). edge((1,2))."])


def test_disable_auto_blacklist():
    context = Context()

    @validate(context=context, auto_blacklist=False)
    class Edge:
        source: int
        dest: int

    assert str(context.run_solver(["edge(1,2). edge((1,2))."])) == '[edge(1,2), edge((1,2))]'


def test_class_can_have_attributes():
    context = Context()

    @validate(context=context)
    class Node:
        value: int

        count = [0, 1, 2]   # a way to track the number of instances, and check they are in 1..2

        @classmethod
        def all_instances_known(cls):
            if not (cls.count[1] <= cls.count[0] <= cls.count[2]):
                raise ValueError(f"expecting {cls.count[1]}..{cls.count[2]} instances of {cls.__name__}, "
                                 "but found {cls.count[0]} of them")

        def __post_init__(self):
            self.__class__.count[0] += 1

    with pytest.raises(ValueError):
        Node.all_instances_known()

    Node(Number(1))
    Node.all_instances_known()
    Node(Number(2))
    Node.all_instances_known()

    Node(Number(3))
    with pytest.raises(ValueError):
        Node.all_instances_known()


def test_any_type():
    context = Context()

    @validate(context=context)
    class Weak:
        mystery: Any

    Weak(Number(1))
    Weak(String('abc'))
    Weak(Function('abc'))
    Weak(Function('abc', [Number(1)]))


def test_class_checks():
    context = Context()

    @validate(context=context)
    class Node:
        value: int

        @classmethod
        def check_exactly_two_instances(cls):
            if cls.instances != 2:
                raise ValueError(f"expecting 2 instances of {cls.__name__}, but found {cls.instances} of them")

        def __post_init__(self):
            if self.value <= 0:
                raise ValueError("must be positive")
            self.__class__.instances += 1
    Node.instances = 0

    context.run_grounder(["node(1)."])
    with pytest.raises(ValueError):
        context.run_class_checks()

    context.run_grounder(["node(2)."])
    context.run_class_checks()

    context.run_grounder(["node(3)."])
    with pytest.raises(ValueError):
        context.run_class_checks()
