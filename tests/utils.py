from typing import List

from clingo import Control, SymbolicAtom

from valasp import Context


def run_clingo(context: Context, base_program: List[str]) -> List[SymbolicAtom]:
    control = Control()
    control.add("base", [], '\n'.join(base_program))
    control.add("validators", [], context.validators())
    control.ground([
        ("base", []),
        ("validators", [])
    ], context=context)

    res = []

    def on_model(model):
        nonlocal res
        for atom in model.symbols(atoms=True):
            res.append(atom)

    control.solve(on_model=on_model)
    return res
