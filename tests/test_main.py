import sys
from typing import List

import pytest

from valasp.main import main


def call_main(args: List[str]) -> List[str]:
    sys.argv = ['valasp'] + args
    res = []
    main(res)
    return res


def call_main_on_yaml_and_asp(tmp_path, yaml_content, asp_content) -> List[str]:
    yaml_file = tmp_path / "input.yaml"
    yaml_file.write_text(yaml_content)
    asp_file = tmp_path / "input.asp"
    asp_file.write_text(asp_content)
    return call_main([str(yaml_file), str(asp_file)])


def test_no_args():
    with pytest.raises(SystemExit) as error:
        call_main([])
        assert error.value.code == 1


def test_bday(tmp_path):
    yaml = """
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
    """

    res = call_main_on_yaml_and_asp(tmp_path, yaml, "bday(sofia, (2019,6,25)). bday(leonardo, (2018,2,1)).")
    assert 'All valid!' in res

    res = call_main_on_yaml_and_asp(tmp_path, yaml, "bday(sofia, (2019,6,25)). bday(leonardo, (2018,2,1)). bday(bigel, (1982,123)).")
    assert 'ValueError: expecting arity 3 for TUPLE' in '\n'.join(res)

