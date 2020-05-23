# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

"""The main method when the module is executed as a script is defined here.

Here is an example of usage for a valid file:

.. code-block:: bash

    (valasp) $ cat examples/bday.yaml
    valasp:
        python: |+
            import datetime
        asp: |+

    date:
        year: Integer
        month: Integer
        day: Integer

        valasp:
            is_predicate: False
            with_fun: TUPLE
            after_init: |+
                datetime.datetime(self.year, self.month, self.day)

    bday:
        name:
            type: Alpha
            min: 3
        date: date

    (valasp) $ cat examples/bday.valid.asp
    bday(sofia, (2019,6,25)).
    bday(leonardo, (2018,2,1)).

    (valasp) $ python -m valasp examples/bday.yaml examples/bday.valid.asp
    Answer: bday(sofia,(2019,6,25)) bday(leonardo,(2018,2,1))


And here is an example of invalid file:

.. code-block:: bash

    (valasp) $ cat examples/bday.invalid.asp
    bday(sofia, (2019,6,25)).
    bday(leonardo, (2018,2,1)).
    bday(bigel, (1982,123)).

    (valasp) $ python -m valasp examples/bday.yaml examples/bday.invalid.asp
    <block>:31:17-51: error: error in context:
      Traceback (most recent call last):
        File "<def valasp_validate_bday(value)>", line 2, in valasp_validate_bday
        File "<def Bday.__init__(self, value)>", line 16, in Bday____init__
        File "<def Date.__init__(self, value)>", line 7, in Date____init__
      ValueError: expecting arity 3 for TUPLE, but found 2


Functions in this module are not intended to be used directly or imported in some other module of this project.
"""

import runpy
import sys
import tempfile
from typing import List, Callable

import yaml

from valasp.translators.yaml2python import Yaml2Python


def parse_args(args, stdout, stderr) -> Callable:
    print_only = False
    for arg in args:
        if arg == '--print':
            print_only = True
            break
    args[:] = filter(lambda arg: arg != '--print', args)

    if len(args) < 1:
        print('To validate a YAML file against one or more ASP files, also running clingo:\n'
              '\tpython -m valasp <YAML file> [ASP files]\n'
              'To produce Python code to ease validation in couple with clingo:\n'
              '\tpython -m valasp --print <YAML file>', file=stderr)
        exit(1)

    if print_only:
        return print_python_code
    return run_clingo


def process_yaml(yaml_file: str) -> List[str]:
    with open(yaml_file) as f:
        yaml_input = yaml.safe_load(f)
        yaml2python = Yaml2Python(yaml_input)
        return yaml2python.convert2python()


def print_python_code(asp_files, validation_code, stdout, stderr):
    if asp_files:
        print(f'# files {asp_files} have been ignored', file=stdout)
    print('\n'.join(validation_code), file=stdout)


def run_clingo(asp_files, validation_code, stdout, stderr):
    with tempfile.NamedTemporaryFile() as validation_file:
        for line in validation_code:
            validation_file.write(line.encode())
        validation_file.seek(0)
        mod = runpy.run_path(path_name=validation_file.name)
        mod['main'](asp_files, stdout, stderr)


def main(args: List[str], stdout=sys.stdout, stderr=sys.stderr):
    callback = parse_args(args, stdout, stderr)

    yaml_file = args[0]
    asp_files = args[1:]

    try:
        validation_code = process_yaml(yaml_file)
        callback(asp_files, validation_code, stdout, stderr)
    except Exception as e:
        print(e, file=stderr)

