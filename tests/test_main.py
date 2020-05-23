from typing import List, Tuple

import pytest

from valasp.main import main


def call_main(tmp_path, args: List[str]) -> Tuple[str, str]:
    stdout = tmp_path / "out"
    stderr = tmp_path / "err"
    main(args, stdout=stdout.open('w'), stderr=stderr.open('w'))
    return stdout.read_text(), stderr.read_text()


def call_main_on_yaml_and_asp(tmp_path, yaml_content: str, asp_content: str = None, for_print: bool = False) -> Tuple[str, str]:
    yaml_file = tmp_path / "input.yaml"
    yaml_file.write_text(yaml_content)
    args = [yaml_file.as_posix()]
    if asp_content:
        asp_file = tmp_path / "input.asp"
        asp_file.write_text(asp_content)
        args.append(asp_file.as_posix())
    if for_print:
        args.append('--print')
    return call_main(tmp_path, args)


def test_no_args(tmp_path):
    with pytest.raises(SystemExit) as error:
        call_main(tmp_path, [])
        assert error.value.code == 1

    with pytest.raises(SystemExit) as error:
        call_main(tmp_path, ['--print'])
        assert error.value.code == 1

    with pytest.raises(SystemExit) as error:
        call_main(tmp_path, ['--print', '--print'])
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

    out, err = call_main_on_yaml_and_asp(tmp_path, yaml, "bday(sofia, (2019,6,25)). bday(leonardo, (2018,2,1)).")
    assert 'All valid!' in out
    assert not err

    out, err = call_main_on_yaml_and_asp(tmp_path, yaml, "bday(sofia, (2019,6,25)). bday(leonardo, (2018,2,1)). bday(bigel, (1982,123)).")
    assert 'ValueError: expecting arity 3 for TUPLE' in err

    out, err = call_main_on_yaml_and_asp(tmp_path, yaml, for_print=True)
    assert 'if len(self.name) < 3: raise ValueError(f"Len should be >= 3. Received: {self.name}")' in out

    out, err = call_main_on_yaml_and_asp(tmp_path, yaml, "ignored file content", for_print=True)
    assert 'have been ignored' in out


def test_wrong_yaml(tmp_path):
    yaml = """
valasp:
    unknown_key: foo
    """
    out, err = call_main_on_yaml_and_asp(tmp_path, yaml)
    assert 'unexpected unknown_key in valasp' in err
