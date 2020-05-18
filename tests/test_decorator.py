import datetime
import pytest
from clingo import Number, Function, Tuple
from clingo import String as QString

from valasp.context import ValAspWarning, Context
from valasp.decorator import validate, Fun
from valasp.domain.primitives import Integer, String, Alpha, Any


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
        first: Integer
        second: Integer

    p12 = Pair(Function('pair', [Number(1), Number(2)]))
    assert str(p12) == 'Pair(1,2)'

    p13 = Pair(Function('pair', [Number(1), Number(3)]))
    p12_ = Pair(Function('pair', [Number(1), Number(2)]))
    assert p12 < p13
    assert p13 > p12
    assert p12 == p12_


def test_int():
    context = Context()

    @validate(context=context)
    class Node:
        value: Integer
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
        value: String
    Name(QString('mario'))

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
        value: Integer

    @validate(context=context, with_fun=Fun.TUPLE)
    class Edge:
        from_: Node
        to: Node

        def check_ordered(self):
            if not(self.from_ < self.to):
                raise ValueError("nodes must be ordered")
    Edge(Tuple([Number(1), Number(2)]))

    model = context.run_solver(['node(1). node(2). edge(1,2).'])
    assert str(model) == '[node(1), node(2), edge(1,2)]'

    with pytest.raises(RuntimeError):
        context.run_solver(['node(1). node(2). edge(2,1).'])


def test_underscore_in_annotations():
    context = Context()

    @validate(context=context)
    class Foo:
        __init__: Integer

    assert str(Foo(Number(1))) == 'Foo(1)'
    assert Foo(Number(1)).__init__ == 1

    @validate(context=context)
    class Bar:
        __str__: Integer

    assert str(Bar(Number(1))) == 'Bar(1)'
    assert Bar(Number(1)).__str__ == 1


def test_auto_blacklist():
    context = Context()

    @validate(context=context, with_fun=Fun.TUPLE)
    class Edge:
        source: Integer
        dest: Integer
    Edge(Tuple([Number(1), Number(2)]))

    assert str(context.run_solver(["edge(1,2)."])) == '[edge(1,2)]'

    with pytest.raises(RuntimeError):
        context.run_solver(["edge(1,2). edge((1,2))."])


def test_disable_auto_blacklist():
    context = Context()

    @validate(context=context, auto_blacklist=False)
    class Edge:
        source: Integer
        dest: Integer
    Edge(Function('edge', [Number(1), Number(2)]))

    assert str(context.run_solver(["edge(1,2). edge((1,2))."])) == '[edge(1,2), edge((1,2))]'


def test_class_can_have_attributes():
    context = Context()

    @validate(context=context)
    class Node:
        value: Integer

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
    Weak(QString('abc'))
    Weak(Function('abc', []))
    Weak(Function('abc', [Number(1)]))


def test_class_checks():
    context = Context()

    @validate(context=context)
    class Node:
        value: Integer

        @classmethod
        def check_exactly_two_instances(cls):
            if cls.instances != 2:
                raise ValueError(f"expecting 2 instances of {cls.__name__}, but found {cls.instances} of them")

        def __post_init__(self):
            self.__class__.instances += 1
    Node.instances = 0

    context.run_grounder(["node(1)."])
    with pytest.raises(ValueError):
        context.run_class_methods()

    context.run_grounder(["node(2)."])
    context.run_class_methods()

    context.run_grounder(["node(3)."])
    with pytest.raises(ValueError):
        context.run_class_methods()


def test_checks_must_have_no_arguments():
    with pytest.warns(ValAspWarning):
        @validate(context=Context())
        class Foo:
            foo: Integer

            def check_fail(self, _):
                raise TypeError()

        with pytest.raises(TypeError):
            Foo(Number(0)).check_fail(0)


def test_is_not_predicate():
    context = Context()

    @validate(context=context, is_predicate=False)
    class Month:
        value: int

        def __post_init__(self):
            if not(1 <= self.value <= 12):
                raise ValueError('month not in 1..12')

    assert str(Month(Number(1))) == 'Month(1)'
    with pytest.raises(ValueError):
        Month(Number(0))
    with pytest.raises(TypeError):
        Month(QString('Sep'))

    @validate(context=context, with_fun=Fun.TUPLE)
    class Salary:
        amount: Integer
        month: Month

    assert str(Salary(Tuple([Number(1000), Number(1)]))) == 'Salary(1000,Month(1))'
    with pytest.raises(ValueError):
        Salary(Tuple([Number(1000), Number(13)]))
    with pytest.raises(TypeError):
        Salary(Tuple([Number(1000), QString('Jan')]))


def test_no_predicate_no_constraint():
    context = Context()

    @validate(context=context, is_predicate=False)
    class Int:
        value: Integer
    Int(Number(1))

    context.run_grounder(['integer(a).'])


def test_with_fun_forward_must_have_arity_one():
    context = Context()

    with pytest.raises(TypeError):
        @validate(context=context, with_fun=Fun.FORWARD)
        class Pair:
            a: Integer
            b: Integer
        Pair(Number(1), Number(2))


def test_complex_implicit_no_predicate():
    context = Context()

    @validate(context=context, is_predicate=False)
    class Date:
        year: int
        month: int
        day: int

        def __post_init__(self):
            datetime.datetime(self.year, self.month, self.day)

    @validate(context=context, with_fun=Fun.TUPLE)
    class Birthday:
        name: String
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
    assert str(Birthday(Tuple([QString('mario'), date]))) == 'Birthday(mario,Date(1983,9,12))'
    with pytest.raises(TypeError):
        Birthday(QString('mario'), Number(0))


def test_no_predicate_with_fun_implicit_no_constraint():
    context = Context()

    @validate(context=context, is_predicate=False, with_fun=Fun.IMPLICIT)
    class Int:
        value: Integer
    Int(Function('int', [Number(1)]))

    context.run_grounder(['int(integer(a)).'])
    context.run_grounder(['int(a).'])


def test_date_as_tuple():
    context = Context()

    @validate(context=context, is_predicate=False, with_fun=Fun.TUPLE)
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
    Birthday(Function('birthday', [QString('mario'), Tuple([Number(1983), Number(9), Number(12)])]))

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

    @validate(context=context, is_predicate=False, with_fun=Fun.IMPLICIT)
    class Date:
        year: int
        month: int
        day: int

        def __post_init__(self):
            datetime.datetime(self.year, self.month, self.day)

    @validate(context=context)
    class Birthday:
        name: String
        date: Date
    Birthday(Function('birthday', [QString('mario'), Function('date', [Number(1983), Number(9), Number(12)])]))

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


def test_with_fun_forward_of_pair():
    context = Context()

    @validate(context=context)
    class Pair:
        a: Integer
        b: Integer

    @validate(context=context)
    class Foo:
        x: Pair

    Foo(Function('pair', [Number(0), Number(1)]))


def test_alpha():
    context = Context()

    @validate(context=context)
    class Id:
        value: Alpha

        def __post_init__(self):
            value = str(self.value)  # not really needed, just to avoid complains from the type hint system
            if not value.islower():
                raise ValueError("I like only lower ids!")

    assert str(Id(Function('ok', []))) == 'Id(ok)'

    with pytest.raises(ValueError):
        Id(Function('Wrong', []))
    with pytest.raises(TypeError):
        Id(QString('wrong'))
