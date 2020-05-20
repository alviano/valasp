ValAsp is validation framework for Answer Set Programming developed by Mario Alviano and Carmine Dodaro.

The idea of ValAsp is to inject validation without cluttering the ASP encoding.
It can be done by decorating Python classes, or by processing a YAML file.
Below are two examples of usage.

.. code-block:: python

    from clingo import Control
    from valasp.context import Context
    from valasp.decorator import validate, Fun

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

    res = None

    def on_model(model):
        nonlocal res
        res = []
        for atom in model.symbols(atoms=True):
            res.append(atom)

    context.run(Control(), on_model, ['birthday("sofia",date(2019,6,25)). birthday("leonardo",date(2018,2,1)).'])
    # res will be [birthday("sofia",date(2019,6,25)), birthday("leonardo",date(2018,2,1))]

    context.run(Control(), aux_program=['birthday("no one",date(2019,2,29)).'])
    # a RuntimeException is raised because the date is not valid
