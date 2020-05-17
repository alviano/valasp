import datetime
import pytest
from clingo import Number, String, Function, Tuple
from typing import Any

from valasp.context import ValAspWarning, Context
from valasp.decorator import validate, Use


def test_must_have_annotations():
    context = Context()

    with pytest.raises(TypeError):
        @validate(context=context)
        class OK:
            pass
        OK()


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
    Node(Number(0))

    model = context.run_solver(["node(0)."])
    assert str(model) == '[node(0)]'

    with pytest.raises(RuntimeError):
        context.run_solver(["node(a)."])


def test_cannot_have_init():
    with pytest.raises(ValueError):
        @validate(context=Context())
        class Node:
            value: int

            def __init__(self):
                self.value = 0
        Node()


def test_check_method():
    context = Context()

    @validate(context=context)
    class Node:
        value: int

        def check(self):
            if not(1 <= self.value <= 10):
                raise ValueError("must be in 1..10")
    Node(Number(1))

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
    Name(String('mario'))

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

        def check_ordered(self):
            if not(self.from_ < self.to):
                raise ValueError("nodes must be ordered")
    Edge(Number(1), Number(2))

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
    Edge(Number(1), Number(2))

    assert str(context.run_solver(["edge(1,2)."])) == '[edge(1,2)]'

    with pytest.raises(RuntimeError):
        context.run_solver(["edge(1,2). edge((1,2))."])


def test_disable_auto_blacklist():
    context = Context()

    @validate(context=context, auto_blacklist=False)
    class Edge:
        source: int
        dest: int
    Edge(Number(1), Number(2))

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
    Weak(Function('abc', []))
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


def test_checks_must_have_no_arguments():
    with pytest.warns(ValAspWarning):
        @validate(context=Context())
        class Foo:
            foo: int

            def check_fail(self, _):
                raise TypeError()

        with pytest.raises(TypeError):
            Foo(Number(0)).check_fail(0)


def test_use_as_value():
    context = Context()

    @validate(context=context, use_as=Use.Value)
    class Month:
        value: int

        def __post_init__(self):
            if not(1 <= self.value <= 12):
                raise ValueError('month not in 1..12')

    assert str(Month(Number(1))) == 'Month(1)'
    with pytest.raises(ValueError):
        Month(Number(0))
    with pytest.raises(TypeError):
        Month(String('Sep'))

    @validate(context=context)
    class Salary:
        amount: int
        month: Month

    assert str(Salary(Number(1000), Number(1))) == 'Salary(1000,Month(1))'
    with pytest.raises(ValueError):
        Salary(Number(1000), Number(13))
    with pytest.raises(TypeError):
        Salary(Number(1000), String('Jan'))


def test_use_as_value_has_no_constraint():
    context = Context()

    @validate(context=context, use_as=Use.Value)
    class Integer:
        value: int
    Integer(Number(1))

    context.run_grounder(['integer(a).'])


def test_use_as_value_must_have_arity_one():
    context = Context()

    with pytest.raises(TypeError):
        @validate(context=context, use_as=Use.Value)
        class Pair:
            a: int
            b: int
        Pair(Number(1), Number(2))


def test_use_as_function():
    context = Context()

    @validate(context=context, use_as=Use.Function)
    class Date:
        year: int
        month: int
        day: int

        def __post_init__(self):
            datetime.datetime(self.year, self.month, self.day)

    @validate(context=context)
    class Birthday:
        name: str
        date: Date

    assert str(Date(Function('date', [Number(1983), Number(9), Number(12)]))) == 'Date(1983,9,12)'
    with pytest.raises(TypeError):
        Date(Number(1983), Number(9), Number(12))
    with pytest.raises(ValueError):
        Date(Tuple([Number(1983), Number(9), Number(12)]))
    with pytest.raises(ValueError):
        Date(Function('date', [Number(1983), Number(9)]))
    with pytest.raises(ValueError):
        Date(Function('data', [Number(1983), Number(9), Number(12)]))

    date = Function('date', [Number(1983), Number(9), Number(12)])
    assert str(Birthday(String('mario'), date)) == 'Birthday(mario,Date(1983,9,12))'
    with pytest.raises(TypeError):
        Birthday(String('mario'), Number(0))


def test_use_as_function_has_no_constraint():
    context = Context()

    @validate(context=context, use_as=Use.Function)
    class Integer:
        value: int
    Integer(Function('integer', [Number(1)]))

    context.run_grounder(['integer(integer(a)).'])
    context.run_grounder(['integer(a).'])


def test_use_as_tuple():
    context = Context()

    @validate(context=context, use_as=Use.Tuple)
    class Date:
        year: int
        month: int
        day: int

        def __post_init__(self):
            datetime.datetime(self.year, self.month, self.day)

    @validate(context=context)
    class Birthday:
        name: str
        date: Date

    assert str(Date(Tuple([Number(1983), Number(9), Number(12)]))) == 'Date(1983,9,12)'
    with pytest.raises(TypeError):
        Date(Number(1982), Number(9), Number(12))
    with pytest.raises(ValueError):
        Date(Tuple([Number(1983), Number(9)]))
    with pytest.raises(ValueError):
        Date(Function('date', [Number(1983), Number(9), Number(12)]))

    date = Tuple([Number(1983), Number(9), Number(12)])
    assert str(Birthday(String('mario'), date)) == 'Birthday(mario,Date(1983,9,12))'
    with pytest.raises(TypeError):
        Birthday(String('mario'), Number(0))


def test_use_as_tuple_has_no_constraint():
    context = Context()

    @validate(context=context, use_as=Use.Tuple)
    class Integer:
        value: int
    Integer(Tuple([Number(1)]))

    context.run_grounder(['integer((a,)).'])
    context.run_grounder(['integer(a).'])


def test_date_as_tuple():
    context = Context()

    @validate(context=context, use_as=Use.Tuple)
    class Date:
        year: int
        month: int
        day: int

        def __post_init__(self):
            datetime.datetime(self.year, self.month, self.day)

    @validate(context=context)
    class Birthday:
        name: str
        date: Date
    Birthday(String('mario'), Tuple([Number(1983), Number(9), Number(12)]))

    model = context.run_solver(['birthday("sofia", (2019,6,25)).'])
    assert str(model) == '[birthday("sofia",(2019,6,25))]'

    model = context.run_solver(['birthday("sofia", (2019,6,25)).', 'birthday("leonardo", (2018,2,1)).'])
    assert str(model) == '[birthday("sofia",(2019,6,25)), birthday("leonardo",(2018,2,1))]'

    with pytest.raises(RuntimeError):
        context.run_solver(['birthday("bigel", (1982,123)).'])
    with pytest.raises(RuntimeError):
        context.run_solver(['birthday("no one", (2019,2,29)).'])
    with pytest.raises(RuntimeError):
        context.run_solver(['birthday("sofia", date(2019,6,25)).'])


def test_date_as_fun():
    context = Context()

    @validate(context=context, use_as=Use.Function)
    class Date:
        year: int
        month: int
        day: int

        def __post_init__(self):
            datetime.datetime(self.year, self.month, self.day)

    @validate(context=context)
    class Birthday:
        name: str
        date: Date
    Birthday(String('mario'), Function('date', [Number(1983), Number(9), Number(12)]))

    model = context.run_solver(['birthday("sofia", date(2019,6,25)).'])
    assert str(model) == '[birthday("sofia",date(2019,6,25))]'

    model = context.run_solver(['birthday("sofia", date(2019,6,25)).', 'birthday("leonardo", date(2018,2,1)).'])
    assert str(model) == '[birthday("sofia",date(2019,6,25)), birthday("leonardo",date(2018,2,1))]'

    with pytest.raises(RuntimeError):
        context.run_solver(['birthday("bigel", date(1982,123)).'])
    with pytest.raises(RuntimeError):
        context.run_solver(['birthday("no one", date(2019,2,29)).'])
    with pytest.raises(RuntimeError):
        context.run_solver(['birthday("sofia", (2019,6,25)).'])
