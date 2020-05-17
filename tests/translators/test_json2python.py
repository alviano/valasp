import sys
from subprocess import Popen, PIPE
from typing import Tuple, List

import pytest

from valasp.main import main


def test_yaml_from_string():
    # add a method to process yaml from string, and also other portions of the code
    # should be unit testable as much as possible
    raise ModuleNotFoundError


def test_main_on_no_args(tmp_path):
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1


def test_main_on_one_arg():
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1


def test_main_on_three_args():
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1


def test_main_on_empty_file(tmp_path):
    inp = tmp_path / "input.yaml"
    inp.write_text('')
    sys.argv = [sys.argv[0], inp, tmp_path / "output.yaml"]
    main()
    # no exception at this level; we have to inform the user


def test_main_on_missing_file(tmp_path):
    sys.argv = [sys.argv[0], tmp_path / "input.yaml", tmp_path / "output.yaml"]
    main()


def run_main_on_yaml(tmp_path, yaml_content) -> str:
    inp = tmp_path / "input.yaml"
    inp.write_text(yaml_content)
    dest = tmp_path / "output.yaml"
    sys.argv = [sys.argv[0], inp, dest]
    main()
    print (dest.read_text())
    return str(dest)


def run_clingo_as_process(files: List[str]) -> Tuple[str, str, int]:
    process = Popen(["clingo"] + files, stdout=PIPE, stderr=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    return output.decode(), err.decode(), exit_code


def write_file(tmp_path, filename: str, content: str) -> str:
    f = tmp_path / filename
    f.write_text(content)
    return str(f)


def test_main_on_yaml_with_errors(tmp_path):
    asp_file = run_main_on_yaml(tmp_path, """
        Foo:
            bar: int
    """)

    (out, err, exit_code) = run_clingo_as_process([
        asp_file,
        write_file(tmp_path, "testcase.asp", "foo(1).")
    ])
    assert exit_code not in [10, 20, 30]
    assert 'syntax error' in err
    assert 'parsing failed' in err


def test_main_on_yaml_valasp_is_not_reserved(tmp_path):
    asp_file = run_main_on_yaml(tmp_path, """
            valasp:
                bar: int
        """)

    (out, err, exit_code) = run_clingo_as_process([
        asp_file,
        write_file(tmp_path, "testcase.asp", "valasp(wrong).")
    ])
    assert exit_code not in [10, 20, 30]
    assert 'TypeError: expecting clingo.SymbolType.Number, but received' in err


def test_main_on_yaml_file_with_one_atom(tmp_path):
    asp_file = run_main_on_yaml(tmp_path, """
        foo:
            bar: int
    """)

    (out, err, exit_code) = run_clingo_as_process([
        asp_file,
        write_file(tmp_path, "testcase.asp", "foo(wrong).")
    ])
    assert exit_code not in [10, 20, 30]
    assert 'TypeError: expecting clingo.SymbolType.Number, but received' in err

    (out, err, exit_code) = run_clingo_as_process([
        asp_file,
        write_file(tmp_path, "testcase.asp", "foo(1).")
    ])
    assert exit_code in [10, 20, 30]
