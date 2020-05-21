ValAsp is validation framework for Answer Set Programming developed by Mario Alviano and Carmine Dodaro.

The idea of ValAsp is to inject validation without cluttering the ASP encoding.
It can be done by decorating Python classes, or by processing a YAML file.
Below is an example usage of the Python layer.

.. code-block:: python

    import datetime

    from clingo import Control
    from valasp.core import Context
    from valasp.domain.primitive_types import Fun, String

    def main():
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

        context.valasp_run(Control(), on_model, ['birthday("sofia",date(2019,6,25)). birthday("leonardo",date(2018,2,1)).'])
        print(res)  # [birthday("sofia",date(2019,6,25)), birthday("leonardo",date(2018,2,1))]

        context.valasp_run(Control(), aux_program=['birthday("no one",date(2019,2,29)).'])
        # a RuntimeException is raised because the date is not valid

    if __name__ == '__main__':
        main()


Attributes can be declared also using ``int`` and ``str``, or the ``clingo`` types.
If you use @-terms, pass them to the ``wrap`` arguments of the constructor, as in the following example.

.. code-block:: python

    from clingo import Control
    from valasp.core import Context


    def prec(x):
        return x.number - 1


    def succ(x):
        return x.number + 1


    def main():
        context = Context(wrap=[prec, succ])  # or wrap=globals().values() to add all function

        @context.valasp()
        class Num:
            value: int


        res = None

        def on_model(model):
            nonlocal res
            res = []
            for atom in model.symbols(atoms=True):
                res.append(atom)

        context.valasp_run(Control(), on_model, ['num(@prec(0)). num(@succ(0)).'])
        print(res)  # [num(1), num(-1)]


    if __name__ == '__main__':
        main()


Even if you opted for putting @-terms in a class, you can still wrap an instance of that class, as done below.

.. code-block:: python

    from clingo import Control
    from valasp.core import Context


    class AtTerms:
        def prec(self, x):
            return x.number - 1


        def succ(self, x):
            return x.number + 1


    def main():
        context = Context(wrap=[AtTerms()])

        @context.valasp()
        class Num:
            value: int


        res = None

        def on_model(model):
            nonlocal res
            res = []
            for atom in model.symbols(atoms=True):
                res.append(atom)

        context.valasp_run(Control(), on_model, ['num(@prec(0)). num(@succ(0)).'])
        print(res)  # [num(1), num(-1)]


    if __name__ == '__main__':
        main()


Another option is to run ``clingo`` with validation:

.. code-block:: python

    #script(python).

    from clingo import Control
    from valasp.core import Context


    def prec(x):
        return x.number - 1


    def succ(x):
        return x.number + 1


    def main(prg):
        context = Context(wrap=[prec, succ])

        @context.valasp()
        class Num:
            value: int

        prg.add("valasp", [], context.valasp_validators())
        prg.ground([('base', []), ('valasp', [])], context=context)
        prg.solve()

    #end.

    num(@prec(0)). num(@succ(0)).
