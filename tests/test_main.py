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
        validate_predicate: False
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
    assert 'ALL VALID!' in out
    assert not err

    out, err = call_main_on_yaml_and_asp(tmp_path, yaml, "bday(sofia, (2019,6,25)). bday(leonardo, (2018,2,1)). bday(bigel, (1982,123)).")
    assert 'expecting arity 3 for TUPLE, but found 2' in out
    assert not err

    out, err = call_main_on_yaml_and_asp(tmp_path, yaml, for_print=True)
    assert 'if len(self.name) < 3: raise ValueError(f"Len should be >= 3. Received: {self.name}")' in out
    assert not err

    out, err = call_main_on_yaml_and_asp(tmp_path, yaml, "ignored file content", for_print=True)
    assert 'have been ignored' in out
    assert not err


def test_wrong_yaml(tmp_path):
    yaml = """
valasp:
    unknown_key: foo
    """
    out, err = call_main_on_yaml_and_asp(tmp_path, yaml)
    assert 'unexpected unknown_key in valasp' in err


def test_max_arity(tmp_path):
    yaml = """
valasp:
    max_arity: 10
    """
    out, err = call_main_on_yaml_and_asp(tmp_path, yaml, for_print=True)
    assert 'context = valasp.core.Context(wrap=[], max_arity=10)' in out
    assert not err


def test_wrap(tmp_path):
    yaml = """
valasp:
    wrap:
        - a
        - b
        - C
    """
    out, err = call_main_on_yaml_and_asp(tmp_path, yaml, for_print=True)
    assert 'context = valasp.core.Context(wrap=[a, b, C], max_arity=16)' in out
    assert not err


def test_wrap_at_terms(tmp_path):
    yaml = """
valasp:
    python: |+
        def succ(x): return x.number + 1
    wrap:
        - succ
    asp:
        a(@succ(0)).
    """
    out, err = call_main_on_yaml_and_asp(tmp_path, yaml)
    assert 'Answer: a(1)' in out
    assert not err


def test_wrap_at_terms_from_external_file(tmp_path):
    at_terms = tmp_path / 'at_terms.py'
    at_terms.write_text('def succ(x): return x.number + 1')
    yaml = f"""
valasp:
    python: |+
        import sys
        sys.path.append('{tmp_path.as_posix()}')
        from at_terms import *    
    wrap:
        - succ
    asp:
        a(@succ(0)).
    """
    out, err = call_main_on_yaml_and_asp(tmp_path, yaml)
    assert 'Answer: a(1)' in out
    assert not err


def test_wrap_at_terms_from_class(tmp_path):
    yaml = f"""
valasp:
    python: |+
        class AtTerms:
            def succ(x): return x.number + 1
    wrap:
        - AtTerms
    asp: a(@succ(0)).
    """
    out, err = call_main_on_yaml_and_asp(tmp_path, yaml)
    assert 'Answer: a(1)' in out
    assert not err


def test_count(tmp_path):
    yaml = f"""
valasp:
    asp: predicate(1..5).
predicate:
    value:
        type: Integer
        count:
            min: 10
            max: 1002
    """
    out, err = call_main_on_yaml_and_asp(tmp_path, yaml)
    assert 'count of value in predicate predicate cannot reach 10' in out
    assert not err


def test_after_grounding(tmp_path):
    yaml = """
valasp:
    asp: {}
person:
    name: Alpha
    valasp:
        after_init: self.__class__.instances += 1
        before_grounding: cls.instances = 0
        after_grounding: |+
            if cls.instances != 2:
                raise ValueError('expecting 2 instances')
    """
    out, err = call_main_on_yaml_and_asp(tmp_path, yaml.format('person(mario). person(carmine).'))
    assert 'ALL VALID' in out
    assert not err

    out, err = call_main_on_yaml_and_asp(tmp_path, yaml.format('person(mario).'))
    assert 'VALIDATION FAILED' in out
    assert 'expecting 2 instances' in out
    assert not err


def test_auto_blacklist(tmp_path):
    yaml = """
    valasp:
        asp: person(mario). person(mar,io).
    person:
        name: Alpha
        valasp:
            auto_blacklist: {}
        """
    out, err = call_main_on_yaml_and_asp(tmp_path, yaml.format('false'))
    assert 'ALL VALID' in out
    assert not err

    out, err = call_main_on_yaml_and_asp(tmp_path, yaml.format('true'))
    assert 'VALIDATION FAILED' in out
    assert 'person/2 is blacklisted' in out
    assert not err
