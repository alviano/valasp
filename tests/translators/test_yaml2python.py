import base64
import sys
from subprocess import Popen, PIPE
from typing import Tuple, List

import pytest

from valasp.main import main
import yaml
from valasp.translators.yaml2python import Symbol, Yaml2Python


def test_symbol_type():
    for i in {'Integer', 'String', 'Any', 'Alpha'}:
        yaml_input = """
        predicate:
            value: %s   
        """ % i
        result = yaml.safe_load(yaml_input)
        obj = Symbol(result["predicate"], "predicate")
        output = obj.convert2python()
        assert "class Predicate:" in output
        assert "\tvalue: %s" % i in output
        assert "\tdef __post_init__(self):" not in output


def test_symbol_custom_invalid():
    for i in {'my', 'Date', 'bday'}:
        yaml_input = """
        predicate:
            value: %s   
        """ % i
        result = yaml.safe_load(yaml_input)
        with pytest.raises(ValueError):
            Symbol(result["predicate"], "predicate")


def test_symbol_custom_invalid_wrong_methods():
    yaml_input = """        
    bday:
        day: Integer
        valasp:
            is_predicate: False   

    predicate:
        value: my   
    """
    with pytest.raises(ValueError):
        result = yaml.safe_load(yaml_input)
        Symbol(result["predicate"], "predicate")


def test_symbol_min_max():
    yaml_input = """
    predicate:
        value:
            type: Integer
            min: 10   
            max: 100
    """
    result = yaml.safe_load(yaml_input)
    obj = Symbol(result["predicate"], "predicate")
    output = obj.convert2python()
    assert "class Predicate:" in output
    assert "\tvalue: Integer" in output
    assert "\tdef __post_init__(self):" in output
    found_element = False
    for i in output:
        if i.startswith("\t\tif self.value < 10: raise ValueError"):
            found_element = True
    assert found_element
    found_element = False
    for i in output:
        if i.startswith("\t\tif self.value > 100: raise ValueError"):
            found_element = True
    assert found_element


def test_symbol_enum():
    yaml_input = """
    predicate:
        value:
            type: Integer
            enum: [1, 2, 3]
    """
    result = yaml.safe_load(yaml_input)
    obj = Symbol(result["predicate"], "predicate")
    output = obj.convert2python()
    assert "class Predicate:" in output
    assert "\tvalue: Integer" in output
    assert "\tdef __post_init__(self):" in output
    found_element = False
    for i in output:
        if i.startswith("\t\tif self.value not in {1, 2, 3}: raise ValueError"):
            found_element = True
    assert found_element


def test_symbol_enum():
    yaml_input = """
    predicate:
        value:
            type: String
            enum: ['a']
    """
    result = yaml.safe_load(yaml_input)
    obj = Symbol(result["predicate"], "predicate")
    output = obj.convert2python()
    assert "class Predicate:" in output
    assert "\tvalue: String" in output
    assert "\tdef __post_init__(self):" in output
    found_element = False
    for i in output:
        if i.startswith("\t\tif self.value not in {_(%s)}: raise ValueError" % base64.b64encode(str("a").encode())):
            found_element = True
    assert found_element


def test_symbol_sum_positive():
    yaml_input = """
    predicate:
        value:
            type: Integer
            sum+:
                min: 10
                max: 100
    """
    result = yaml.safe_load(yaml_input)
    obj = Symbol(result["predicate"], "predicate")
    output = obj.convert2python()
    assert "class Predicate:" in output
    assert "\tvalue: Integer" in output
    assert "\tdef __post_init__(self):" in output
    assert "\t\tif self.value > 0:" in output
    assert "\t\t\tself.__class__.sum_positive_of_value += self.value" in output
    assert "\tdef before_grounding_init_positive_sum_value(cls): cls.sum_positive_of_value = 0" in output
    assert "\tdef after_grounding_check_positive_sum_value(cls):" in output
    assert "\t\tif cls.sum_positive_of_value > 100: raise ValueError('sum of value in predicate predicate may exceed 100')" in output
    assert "\t\tif cls.sum_positive_of_value < 10: raise ValueError('sum of value in predicate predicate cannot reach 10')" in output


def test_symbol_sum_negative():
    yaml_input = """
    predicate:
        value:
            type: Integer
            sum-:
                min: -100
                max: -10
    """
    result = yaml.safe_load(yaml_input)
    obj = Symbol(result["predicate"], "predicate")
    output = obj.convert2python()
    assert "class Predicate:" in output
    assert "\tvalue: Integer" in output
    assert "\tdef __post_init__(self):" in output
    assert "\t\tif self.value < 0:" in output
    assert "\t\t\tself.__class__.sum_negative_of_value += self.value" in output
    assert "\tdef before_grounding_init_negative_sum_value(cls): cls.sum_negative_of_value = 0" in output
    assert "\tdef after_grounding_check_negative_sum_value(cls):" in output
    assert "\t\tif cls.sum_negative_of_value < -100: raise ValueError('sum of value in predicate predicate may exceed -100')" in output
    assert "\t\tif cls.sum_negative_of_value > -10: raise ValueError('sum of value in predicate predicate cannot reach -10')" in output


def test_symbol_count():
    for i in {'Integer', 'Any', 'String', 'Alpha'}:
        yaml_input = """
        predicate:
            value:
                type: %s
                count:
                    min: 10
                    max: 100
        """ % i
        result = yaml.safe_load(yaml_input)
        obj = Symbol(result['predicate'], 'predicate')
        output = obj.convert2python()
        assert "class Predicate:" in output
        assert "\tvalue: %s" % i in output
        assert "\tdef __post_init__(self):" in output
        assert "\t\tself.__class__.count_of_value += 1" in output
        assert "\tdef before_grounding_init_count_value(cls): cls.count_of_value = 0" in output
        assert "\tdef after_grounding_check_count_value(cls):" in output
        assert "\t\tif cls.count_of_value > 100: raise ValueError('count of value in predicate predicate may exceed 100')" in output
        assert "\t\tif cls.count_of_value < 10: raise ValueError('count of value in predicate predicate cannot reach 10')" in output


def test_symbol_having():
    for i in {"Integer", "String", "Alpha", "Any"}:
        for oper in {"==", "!=", ">", ">=", "<", "<="}:
            yaml_input = """
             predicate:
                 first: %s
                 second: %s
                 valasp:
                     having:
                        - first %s second                  
             """ % (i, i, oper)
            result = yaml.safe_load(yaml_input)
            obj = Symbol(result["predicate"], "predicate")
            output = obj.convert2python()
            assert "class Predicate:" in output
            assert "\tvalue: first" in output
            assert "\tvalue: second" in output
            assert "\tdef __post_init__(self):" in output
            assert "\t\tif self.first %s self.second: raise ValueError" % oper in output

