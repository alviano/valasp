import datetime
import pytest
from clingo import Number, Symbol, Control, Function, Tuple
from clingo import String as QString

from valasp.core import Context
from valasp.domain.names import PredicateName
from valasp.domain.primitive_types import Integer, String, Fun, Any, Alpha
from valasp.domain.raisers import ValAspWarning


def test_max_arity_must_be_positive():
    with pytest.raises(ValueError):
        Context(max_arity=0)


def test_clingo_is_reserved():
    assert Context().valasp_is_reserved('clingo')
    with pytest.raises(KeyError):
        Context().valasp_register_term('filename', PredicateName('clingo'), [], [])
    with pytest.raises(TypeError) as error:
        Context().clingo()
        assert "'module' object is not callable" in error


def test_missing_at_term():
    with pytest.raises(AttributeError) as error:
        Context().missing_at_term()
        assert "object has no attribute 'missing_at_term'" in error


def test_make_fun_successor():
    context = Context()
    successor = context.valasp_make_fun('filename', 'successor', ['x'], ['return x + 1'])
    assert successor(0) == 1
    assert successor(99) == 100


def test_make_fun_can_access_symbol_type():
    context = Context()
    is_number = context.valasp_make_fun('filename', 'is_number', ['x'], ['return x.type == clingo.SymbolType.Number'])
    assert is_number(Number(1))


def test_register_class():
    class Sum:
        def __init__(self):
            self.value = 0

        def add(self, x: int) -> None:
            self.value += x

    context = Context()
    context.valasp_register_class(Sum)
    sum_first = context.valasp_make_fun('filename', 'sum_first', ['n'], [
        'res = Sum()',
        'for i in range(n):',
        '    res.add(i)',
        'return res.value'
    ])
    assert sum_first(10) == sum(range(10))


def test_register_class_with_reserved_name():
    class A:
        a: int

    context = Context()
    context.valasp_register_class(A)
    with pytest.raises(KeyError):
        context.valasp_register_class(A)

    with pytest.raises(ValueError):
        class clingo:
            a: int

        context.valasp_register_class(clingo)


def test_run_solver():
    context = Context()
    assert str(context.valasp_run_solver(["hello_world."])) == "[hello_world]"


def test_register_term():
    context = Context()
    context.valasp_register_term('filename', PredicateName('successor'), ['x'], ['return x.number + 1'])
    model = context.valasp_run_solver(["one(@successor(0))."])
    assert str(model) == '[one(1)]'


def test_add_validator():
    class PositiveNumber:
        def __init__(self, value: Symbol):
            if not(1 <= value.number):
                raise ValueError("not a positive number")
            self.value = value

    context = Context()
    context.valasp_register_class(PositiveNumber)
    context.valasp_add_validator(PredicateName('positiveNumber'), 1)
    model = context.valasp_run_solver(["positiveNumber(1)."])
    assert str(model) == '[positiveNumber(1)]'

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(["positiveNumber(0)."])


def test_blacklist():
    context = Context()
    context.valasp_blacklist(PredicateName('number'), [2])

    model = context.valasp_run_solver(["number(1)."])
    assert str(model) == "[number(1)]"

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(["number(1,2)."])


def test_blacklist_all_arities():
    context = Context()
    context.valasp_blacklist(PredicateName('number'))
    with pytest.raises(RuntimeError):
        context.valasp_run_solver(["number(1)."])


def test_cannot_blacklist_arity_zero():
    with pytest.raises(ValueError):
        Context().valasp_blacklist(PredicateName('foo'), [0])


def test_run_class_checks():
    class Foo:
        def __init__(self, _: Symbol):
            Foo.instances += 1
            self.check_foo()

        @classmethod
        def check_exactly_two_instances(cls):
            if Foo.instances != 2:
                raise ValueError("please, define exactly two instances")

        def check_foo(self):
            pass
    Foo.instances = 0

    context = Context()
    context.valasp_register_class(Foo)
    context.valasp_add_validator(PredicateName('foo'), 1)

    with pytest.raises(ValueError):
        Foo(Number(1))
        context.valasp_run_class_methods()

    Foo(Number(2))
    context.valasp_run_class_methods()

    with pytest.raises(ValueError):
        Foo(Number(3))
        context.valasp_run_class_methods()


def test_class_checks_must_have_no_arguments():
    class Foo:
        @classmethod
        def check_fail(cls, _):
            raise TypeError()

    context = Context()
    context.valasp_register_class(Foo)

    with pytest.raises(TypeError):
        Foo.check_fail(0)

    with pytest.warns(ValAspWarning):
        context.valasp_run_class_methods()


def test_fail_after_grounding():
    context = Context()

    class Foo:
        @classmethod
        def after_grounding(cls):
            raise ValueError('so nice')

    context.valasp_register_class(Foo)

    context.valasp_run(Control(), with_validators=False)
    context.valasp_run(Control(), with_validators=False, with_solve=False)

    with pytest.raises(ValueError):
        context.valasp_run(Control(), with_validators=True)

    with pytest.raises(ValueError):
        context.valasp_run(Control(), with_validators=True, with_solve=True)


def test_wrap_context_object():
    class MyContext:
        def foo(self, x):
            return x.number + 1

    context = Context(wrap=[MyContext()])
    assert str(context.valasp_run_solver(['a(@foo(1)).'])) == '[a(2)]'


def test_global_methods_are_at_terms():
    def foo(x, y):
        return x.number + y.number

    assert str(Context(wrap=[foo]).valasp_run_solver(['a(@foo(1,1)).'])) == '[a(2)]'


def test_valasp_prefix_is_reserved():
    context = Context()
    assert context.valasp_is_reserved('valasp')



def test_must_have_annotations():
    context = Context()

    with pytest.raises(TypeError):
        @context.valasp()
        class OK:
            pass
        OK()


def test_define_str_and_cmp():
    context = Context()

    @context.valasp()
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

    @context.valasp()
    class Node:
        value: Integer
    Node(Number(0))

    model = context.valasp_run_solver(["node(0)."])
    assert str(model) == '[node(0)]'

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(["node(a)."])


def test_cannot_have_init():
    context = Context()
    with pytest.raises(ValueError):
        @context.valasp()
        class Node:
            value: int

            def __init__(self):
                self.value = 0
        Node()


def test_check_method():
    context = Context()

    @context.valasp()
    class Node:
        value: int

        def check(self):
            if not(1 <= self.value <= 10):
                raise ValueError("must be in 1..10")
    Node(Number(1))

    model = context.valasp_run_solver(["node(10)."])
    assert str(model) == '[node(10)]'

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(["node(0)."])

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(["node(11)."])


def test_string():
    context = Context()

    @context.valasp()
    class Name:
        value: String
    Name(QString('mario'))

    model = context.valasp_run_solver(['name("mario").'])
    assert str(model) == '[name("mario")]'

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(["name(mario)."])

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(["name(123)."])


def test_complex_type():
    context = Context()

    @context.valasp()
    class Node:
        value: Integer

    @context.valasp(with_fun=Fun.TUPLE)
    class Edge:
        from_: Node
        to: Node

        def check_ordered(self):
            if not(self.from_ < self.to):
                raise ValueError("nodes must be ordered")
    Edge(Tuple([Number(1), Number(2)]))

    model = context.valasp_run_solver(['node(1). node(2). edge(1,2).'])
    assert str(model) == '[node(1), node(2), edge(1,2)]'

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(['node(1). node(2). edge(2,1).'])


def test_underscore_in_annotations():
    context = Context()

    @context.valasp()
    class Foo:
        __init__: Integer

    assert str(Foo(Number(1))) == 'Foo(1)'
    assert Foo(Number(1)).__init__ == 1

    @context.valasp()
    class Bar:
        __str__: Integer

    assert str(Bar(Number(1))) == 'Bar(1)'
    assert Bar(Number(1)).__str__ == 1


def test_auto_blacklist():
    context = Context()

    @context.valasp(with_fun=Fun.TUPLE)
    class Edge:
        source: Integer
        dest: Integer
    Edge(Tuple([Number(1), Number(2)]))

    assert str(context.valasp_run_solver(["edge(1,2)."])) == '[edge(1,2)]'

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(["edge(1,2). edge((1,2))."])


def test_disable_auto_blacklist():
    context = Context()

    @context.valasp(auto_blacklist=False)
    class Edge:
        source: Integer
        dest: Integer
    Edge(Function('edge', [Number(1), Number(2)]))

    assert str(context.valasp_run_solver(["edge(1,2). edge((1,2))."])) == '[edge(1,2), edge((1,2))]'


def test_class_can_have_attributes():
    context = Context()

    @context.valasp()
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

    @context.valasp()
    class Weak:
        mystery: Any

    Weak(Number(1))
    Weak(QString('abc'))
    Weak(Function('abc', []))
    Weak(Function('abc', [Number(1)]))


def test_class_checks():
    context = Context()

    @context.valasp()
    class Node:
        value: Integer

        @classmethod
        def check_exactly_two_instances(cls):
            if cls.instances != 2:
                raise ValueError(f"expecting 2 instances of {cls.__name__}, but found {cls.instances} of them")

        def __post_init__(self):
            self.__class__.instances += 1
    Node.instances = 0

    context.valasp_run_grounder(["node(1)."])
    with pytest.raises(ValueError):
        context.valasp_run_class_methods()

    context.valasp_run_grounder(["node(2)."])
    context.valasp_run_class_methods()

    context.valasp_run_grounder(["node(3)."])
    with pytest.raises(ValueError):
        context.valasp_run_class_methods()


def test_checks_must_have_no_arguments():
    context = Context()
    with pytest.warns(ValAspWarning):
        @context.valasp()
        class Foo:
            foo: Integer

            def check_fail(self, _):
                raise TypeError()

        with pytest.raises(TypeError):
            Foo(Number(0)).check_fail(0)


def test_is_not_predicate():
    context = Context()

    @context.valasp(is_predicate=False)
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

    @context.valasp(with_fun=Fun.TUPLE)
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

    @context.valasp(is_predicate=False)
    class Int:
        value: Integer
    Int(Number(1))

    context.valasp_run_grounder(['integer(a).'])


def test_with_fun_forward_must_have_arity_one():
    context = Context()

    with pytest.raises(TypeError):
        @context.valasp(with_fun=Fun.FORWARD)
        class Pair:
            a: Integer
            b: Integer
        Pair(Number(1), Number(2))


def test_complex_implicit_no_predicate():
    context = Context()

    @context.valasp(is_predicate=False)
    class Date:
        year: int
        month: int
        day: int

        def __post_init__(self):
            datetime.datetime(self.year, self.month, self.day)

    @context.valasp(with_fun=Fun.TUPLE)
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

    @context.valasp(is_predicate=False, with_fun=Fun.IMPLICIT)
    class Int:
        value: Integer
    Int(Function('int', [Number(1)]))

    context.valasp_run_grounder(['int(integer(a)).'])
    context.valasp_run_grounder(['int(a).'])


def test_date_as_tuple():
    context = Context()

    @context.valasp(is_predicate=False, with_fun=Fun.TUPLE)
    class Date:
        year: int
        month: int
        day: int

        def __post_init__(self):
            datetime.datetime(self.year, self.month, self.day)

    @context.valasp()
    class Birthday:
        name: str
        date: Date
    Birthday(Function('birthday', [QString('mario'), Tuple([Number(1983), Number(9), Number(12)])]))

    model = context.valasp_run_solver(['birthday("sofia", (2019,6,25)).'])
    assert str(model) == '[birthday("sofia",(2019,6,25))]'

    model = context.valasp_run_solver(['birthday("sofia", (2019,6,25)).', 'birthday("leonardo", (2018,2,1)).'])
    assert str(model) == '[birthday("sofia",(2019,6,25)), birthday("leonardo",(2018,2,1))]'

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(['birthday("bigel", (1982,123)).'])
    with pytest.raises(RuntimeError):
        context.valasp_run_solver(['birthday("no one", (2019,2,29)).'])
    with pytest.raises(RuntimeError):
        context.valasp_run_solver(['birthday("sofia", date(2019,6,25)).'])


def test_date_as_fun():
    context = Context()

    @context.valasp(is_predicate=False, with_fun=Fun.IMPLICIT)
    class Date:
        year: int
        month: int
        day: int

        def __post_init__(self):
            datetime.datetime(self.year, self.month, self.day)

    @context.valasp()
    class Birthday:
        name: String
        date: Date
    Birthday(Function('birthday', [QString('mario'), Function('date', [Number(1983), Number(9), Number(12)])]))

    model = context.valasp_run_solver(['birthday("sofia", date(2019,6,25)).'])
    assert str(model) == '[birthday("sofia",date(2019,6,25))]'

    model = context.valasp_run_solver(['birthday("sofia", date(2019,6,25)).', 'birthday("leonardo", date(2018,2,1)).'])
    assert str(model) == '[birthday("sofia",date(2019,6,25)), birthday("leonardo",date(2018,2,1))]'

    with pytest.raises(RuntimeError):
        context.valasp_run_solver(['birthday("bigel", date(1982,123)).'])
    with pytest.raises(RuntimeError):
        context.valasp_run_solver(['birthday("no one", date(2019,2,29)).'])
    with pytest.raises(RuntimeError):
        context.valasp_run_solver(['birthday("sofia", (2019,6,25)).'])


def test_with_fun_forward_of_pair():
    context = Context()

    @context.valasp()
    class Pair:
        a: Integer
        b: Integer

    @context.valasp()
    class Foo:
        x: Pair

    Foo(Function('pair', [Number(0), Number(1)]))


def test_alpha():
    context = Context()

    @context.valasp()
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


def test_sum_of_salaries():
    context = Context()

    @context.valasp()
    class Income:
        company: str  # String
        amount: int  # Integer

        def __post_init__(self):
            if not(self.amount > 0):
                raise ValueError("amount must be positive")
            self.__class__.amount_sum += self.amount
            if self.__class__.amount_sum > Integer.max():
                raise OverflowError(f"sum of amount may exceed {Integer.max()}")

        @classmethod
        def before_grounding_init_amount_sum(cls):
            cls.amount_sum = 0

        @classmethod
        def after_grounding_check_amount_sum(cls):
            if cls.amount_sum < 10000:
                raise ValueError(f"sum of amount cannot reach 10000")
            if cls.amount_sum == 3000000000:
                raise OverflowError(f"catch this!")

    control = Control()
    control.add("base", [], 'income("Acme ASP",1500000000). income("Yoyodyne YAML",1500000000).')
    control.add("valasp", [], context.valasp_validators())
    context.valasp_run_class_methods('before_grounding')
    with pytest.raises(RuntimeError):
        control.ground([("base", []), ("valasp", [])], context=context)
    with pytest.raises(OverflowError):
        context.valasp_run_class_methods('after_grounding')


def test_doc_example():
    context = Context()

    @context.valasp(is_predicate=False, with_fun=Fun.IMPLICIT)
    class Date:
        year: int
        month: int
        day: int

        def __post_init__(self):
            datetime.datetime(self.year, self.month, self.day)

    @context.valasp()
    class Birthday:
        name: String
        date: Date

    res = None

    def on_model(model):
        nonlocal res
        res = []
        for atom in model.symbols(atoms=True):
            res.append(atom)

    context.valasp_run(Control(), on_model=on_model, aux_program=['birthday("sofia",date(2019,6,25)). birthday("leonardo",date(2018,2,1)).'])
    assert str(res) == '[birthday("sofia",date(2019,6,25)), birthday("leonardo",date(2018,2,1))]'

    with pytest.raises(RuntimeError):
        context.valasp_run(Control(), aux_program=['birthday("no one",date(2019,2,29)).'])
