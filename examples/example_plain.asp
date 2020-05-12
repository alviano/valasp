#script(python).

import clingo
import re

from valasp import Context, validate
from typing import Callable


context = Context()
context.blacklist('_foo', [1])


@validate(context=context)
class Node:
    value: int

    def __post_init__(self):
        if not (0 <= self.value <= 999999):
            raise ValueError("node not in 0..999999")

    #def __str__(self):
    #    return f"A node with id {self.value}"


@validate(context=context)
class Edge:
    from_: Node
    to: Node

    def __post_init__(self):
        if not (self.from_ < self.to):
            raise ValueError(f'the first argument must be smaller than the second argument, but {self}')


@validate(context=context)
class Foo:
    bar: Callable
    buzz: str

    def __post_init__(self):
        if not (0 <= len(self.bar.arguments)):
            raise ValueError("foo must receive a constant")
        if not re.fullmactch(r'car[a-z]*', self.bar.name):
            raise ValueError("does not match!")


@validate(context=context)
class Make_fun:
    bar: int

#@validate(context=context)
#class Fake:
#    pass


def main(prg):
    prg.add("validators", [], context.validators())
    prg.ground([
        ("base", []),
        ("validators", []),
    ], context=context)
    prg.solve()

#end.

node(1).
%node("carmine").

node(1,2).

edge(1,2).
%edge(2,1).

%foo(carmine, "Carmine").
%foo(carmine(a)).
%foo(mario, "Mario").

%_foo(10).