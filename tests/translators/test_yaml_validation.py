import sys
from subprocess import Popen, PIPE
from typing import Tuple, List

import pytest
import yaml

from valasp.translators.yaml_validation import YamlValidation


def test_yaml_invalid_root():
    for i in ['Integer', 'VALASP', 10, ['a', 'b']]:
        yaml_input = """
                %s
                """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate(yaml.safe_load(yaml_input))


def test_yaml_valasp_in_user_defined_module():
    yaml_input = """
    having:
        equals:
            - [first, second]
            - [first2, second]
        different:
            - [first, second]
            - [first2, second]
        gt:
            - [first, second]
            - [first2, second]
        ge:
            - [first, second]
            - [first2, second]
        lt:
            - [first, second]
            - [first2, second]
        le:
            - [first, second]
            - [first2, second]
    validate_predicate: True
    with_fun: FORWARD_IMPLICIT
    auto_blacklist: True
    after_init: |+
        code
        to
        add
        at
        the
        end
        of
        __post_init__
    before_grounding: |+
        cls.instances = set()
    after_grounding: |+
        if len(cls.instances()) < 10:
            raise ...
    """
    YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_valasp_in_user_defined_module():
    yaml_input = """
    valasp:
        having:
            - first == second
            - first2 != second
            - first3 < second
            - first3 <= second
            - first3 > second
            - first3 >= second
            - first    ==     second
            - first==second   
            - first  >=second
            - first>=second        
        validate_predicate: True        
    """
    YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_valasp_in_user_defined_module_2():
    for i in {"Integer", "String", "Alpha", "Any"}:
        for oper in {"==", "!=", ">", ">=", "<", "<=", " == ", " !=", "> ", "  >=", "<  ", "  <=  "}:
            yaml_input = """
             predicate:
                 first: %s
                 second: %s
                 valasp:
                     having:
                        - first%ssecond                  
             """ % (i, i, oper)
            YamlValidation.validate(yaml.safe_load(yaml_input))


def test_yaml_having_valasp_in_user_defined_module_wrong_keyword():
    for i in {'different', '<>', '=', '>>'}:
        yaml_input = """
            having:
                - first %s second            
            """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_having_valasp_in_user_defined_module_wrong_name():
    for i in {'>', '==', '!=', '<='}:
        yaml_input = """
            having:
                - First %s second       
            """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))

    for i in {'>', '==', '!=', '<='}:
        yaml_input = """
            having:
                - first %s Second       
            """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_having_valasp_not_a_list():
    for i in [10, '1', {'first': 0}]:
        yaml_input = """
            having: %s              
            """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_having_valasp_in_user_defined_module_not_a_list():
    yaml_input = """
        having:            
            different: Integer                
        """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_having_valasp_in_user_defined_module_not_valid_split():
    for i in ['first == second == third', ['a', 'b'], 'first of == second']:
        yaml_input = """
            having:
                - %s
            """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_having_valasp_in_user_defined_module_complex_usage():
    yaml_input = """
        having:
            equals:
                - [first, second, third]
                - [first2, second]
            different:
                - [first, second]
                - [first2, second]
        """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_having_valasp_in_user_defined_module_missing_list():
    yaml_input = """
        having:
            equals:                
            different:
                - [first, second]
                - [first2, second]
        """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_validate_predicate_correct_bool():
    for i in {'True', 'true', 'TRUE'}:
        yaml_input = """
            validate_predicate: %s
            """ % i
        YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_validate_predicate_not_bool():
    for i in [0, 1, {'dict': 0}]:
        yaml_input = """
            validate_predicate: %s
            """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_validate_predicate_mispelled_true():
    for i in {'TRue', 'TrUE', 'TruE', 'trUe', 'truE'}:
        yaml_input = """
            validate_predicate: %s
            """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_with_fun_correct():
    for i in {'FORWARD_IMPLICIT', 'FORWARD', 'IMPLICIT', 'TUPLE'}:
        yaml_input = """
            with_fun: %s
            """ % i
        YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_with_fun_wrong_keyword():
    for i in {'FORWARDIMPLICIT', 'WOW', 'forward', 'Implicit', '_TUPLE'}:
        yaml_input = """
            with_fun: %s
            """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_auto_blacklist_correct_bool():
    for i in {'False', 'false', 'FALSE'}:
        yaml_input = """
            auto_blacklist: %s
            """ % i
        YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_auto_blacklist_not_bool():
    for i in [0, 1, {'dict': 0}]:
        yaml_input = """
            auto_blacklist: %s
            """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_auto_blacklist_mispelled_false():
    for i in {'falSe', 'FAlse', 'FaLSE', 'FalsE', 'falsE'}:
        yaml_input = """
            validate_predicate: %s
            """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_after_init():
    yaml_input = """
    after_init: |+
        code to add at the end of __post_init__
    """
    YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_after_init_wrong_type():
    yaml_input = """
    after_init: [1,2,3]       
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_before_grounding():
    yaml_input = """
    before_grounding: |+
        code to execute after grounding
    """
    YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_before_grounding_wrong_type():
    yaml_input = """
    before_grounding: [1,2,3]       
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_after_grounding():
    yaml_input = """
    after_grounding: |+
        code to execute after grounding
    """
    YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_after_grounding_wrong_type():
    yaml_input = """
    after_grounding: [1,2,3]       
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp_in_symbol(yaml.safe_load(yaml_input))


def test_yaml_valasp():
    yaml_input = """
    python: |+
        for i in range(10):
            print(i)
    asp: |+
        code
    
    wrap:
        - a
        - B
        - lower
        - Upper
        
    max_arity: 10
    """
    YamlValidation.validate_valasp(yaml.safe_load(yaml_input))


def test_yaml_valasp_max_arity_wrong_types():
    for i in ['a', -1, 100, {'a': 1}, [1]]:
        yaml_input = """
        max_arity: %s
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp(yaml.safe_load(yaml_input))


def test_yaml_valasp_wrap_not_list():
    for i in ['a', 1, {'a': 1}]:
        yaml_input = """    
        wrap: %s            
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_valasp(yaml.safe_load(yaml_input))


def test_yaml_valasp_not_predicate():
    yaml_input = """    
    wrap:
        - a a        
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp(yaml.safe_load(yaml_input))


def test_yaml_valasp_root():
    yaml_input = """
    valasp:
        python: |+
            for i in range(10):
                print(i)
        asp: |+
            code
    """
    YamlValidation.validate(yaml.safe_load(yaml_input))


def test_yaml_valasp_wrong_keyword():
    yaml_input = """
    python: |+
        for i in range(10):
            print(i)
    ASP: |+
        code
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp(yaml.safe_load(yaml_input))


def test_yaml_valasp_asp_wrong_type():
    yaml_input = """
    python: |+
        for i in range(10):
            print(i)
    asp:
        something:
            here
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp(yaml.safe_load(yaml_input))


def test_yaml_valasp_python_wrong_type():
    yaml_input = """
    python:
        - something
        - here
    asp: |+
        a(X) :- b(X).
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp(yaml.safe_load(yaml_input))


def test_yaml_valasp_python_wrong_type():
    yaml_input = """
    python:
        - something
        - here
    asp: |+
        a(X) :- b(X).
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_valasp(yaml.safe_load(yaml_input))


def test_yaml_symbol_name():
    for i in {'predicate', '_predicate', '_preDicate', '___predicate', '"on"', '"off"'}:
        yaml_input = """
        %s:
            term1: Integer
        """ % i
        YamlValidation.validate(yaml.safe_load(yaml_input))


def test_yaml_symbol_name_invalid_names():
    for i in ['Name', 'Valasp', 'valasp', 'on', 'off', 1, -2, ['name'], '"1"', "_Predicate"]:
        yaml_input = """
        Name:
            term1: Integer
        """
        with pytest.raises(ValueError):
            YamlValidation.validate(yaml.safe_load(yaml_input))


def test_yaml_symbol_name_not_a_dictionary():
    for i in ['Integer', 'String', 'pred', ['a', 'b']]:
        yaml_input = """
        predicate: %s             
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate(yaml.safe_load(yaml_input))


def test_yaml_term_type_declaration():
    for i in {'Integer', 'String', 'Alpha', 'Any', 'predicate', '_predicate', '_preDicate', '___predicate', '"on"', '"off"'}:
        yaml_input = """
        term1: %s
        """ % i
        YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_invalid_term_types():
    for i in ['Name', 'Valasp', 'on', 'off', 1, -2, ['name'], '"1"', "_Predicate"]:
        yaml_input = """
        term1: %s
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_integer_declaration():
    yaml_input = """
    term_name_6:
        type: Integer
        min: 0
        max: 99
        sum+:
            min: 0
            max: 1000
        sum-:
            min: -1000
            max: -10
        count:
            min: 10
            max: 100
        sum+: Integer
        enum: [1, 2, 3]
    """
    YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_integer_min_greater_than_max():
    yaml_input = """
    term_name_6:
        type: Integer
        min: 20
        max: 10        
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_integer_declaration_no_type():
    yaml_input = """
    term_name_6:
        min: 0
        max: 99
        sum+:
            min: 0
            max: 1000
        sum-:
            min: 0
            max: -1000
        count:
            min: 10
            max: 100
        sum+: Integer
        enum: [1, 2, 3]
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_integer_declaration_wrong_keyword():
    for j in {'Integer', 'String'}:
        for i in {'MIN', 'minimum'}:
            yaml_input = """
            term_name_6:
                type: %s
                %s: 0
            """ % (j, i)
            with pytest.raises(ValueError):
                YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_integer_declaration_invalid_min():
    for j in {'Integer', 'String'}:
        for i in {1000000000000, 'Integer'}:
            yaml_input = """
            term_name_6:
                type: %s
                min: %s        
            """ % (j, i)
            with pytest.raises(ValueError):
                YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_integer_declaration_invalid_max():
    for i in {1000000000000, 'Integer'}:
        yaml_input = """
        term_name_6:
            type: Integer
            max: %s        
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_integer_declaration_invalid_enum_integer():
    for i in [['1', 2, 3], 1, {'value': 0}]:
        yaml_input = """
        term_name_6:
            type: Integer
            enum: %s
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_integer_declaration_invalid_sum_positive():
    for i in {'String', 'int', 10}:
        yaml_input = """
        term_name_6:
            type: Integer
            sum+: %s                 
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_symbol(yaml.safe_load(yaml_input))

    for i in {100000000000, 'Integer', -5}:
        yaml_input = """
        term_name_6:
            type: Integer
            sum+:
                min: 0
                max: %s  
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_symbol(yaml.safe_load(yaml_input))

    for i in {100000000000, 'Integer', -5}:
        yaml_input = """
        term_name_6:
            type: Integer
            sum+:
                min: %s
                max: 10  
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_integer_declaration_invalid_sum_negative():
    for i in {'String', 'int', -10}:
        yaml_input = """
        term_name_6:
            type: Integer
            sum-: %s                 
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_symbol(yaml.safe_load(yaml_input))

    for i in {-10000000000, 'Integer', 10}:
        yaml_input = """
        term_name_6:
            type: Integer
            sum-:
                min: 0
                max: %s  
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_symbol(yaml.safe_load(yaml_input))

    for i in {-10000000000, 'Integer', 10}:
        yaml_input = """
        term_name_6:
            type: Integer
            sum-:
                min: %s
                max: 0  
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_declaration_invalid_count():
    for j in {'Integer', 'String', 'Any', 'Alpha', 'user_defined'}:
        for i in {-5, 100000000000, 'Integer'}:
            yaml_input = """
            term_name_6:
                type: %s
                count:
                    min: %s
                    max: 0  
            """ % (j, i)
            with pytest.raises(ValueError):
                YamlValidation.validate_symbol(yaml.safe_load(yaml_input))

        for i in {-5, 100000000000, 'Integer'}:
            yaml_input = """
            term_name_6:
                type: %s
                count:
                    min: 0
                    max: %s  
            """ % (j, i)
            with pytest.raises(ValueError):
                YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_elements_invalid_declaration():
    for j in {'String', 'Any', 'Alpha', 'user_defined'}:
        for i in {'sum+', 'sum-'}:
            yaml_input = """
            term_name_6:
                type: %s
                %s:
                    min: 0
                    max: 1000
            """ % (j, i)
            with pytest.raises(ValueError):
                YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_string_enum():
    yaml_input = """
    term_name_6:
        type: String
        enum: ['1', '2', '3', 'ok test']
    """
    YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_string_invalid_enum():
    yaml_input = """
    term_name_6:
        type: String
        enum: [1, 'my logic', 'wow']
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_alpha_enum():
    yaml_input = """
    term_name_6:
        type: Alpha
        enum: [logic1, my_logic, well]
    """
    YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_alpha_invalid_enum():
    yaml_input = """
    term_name_6:
        type: Alpha
        enum: [logic1, 'my logic', well]
    """
    with pytest.raises(ValueError):
        YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_alpha_invalid_min():
    for s in {'String', 'Alpha'}:
        for i in [-1, 'a', [1, 2]]:
            yaml_input = """
            term_name_6:
                type: %s
                min: %s
            """ % (s, i)
            with pytest.raises(ValueError):
                YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_pattern():
    for i in {'String', 'Alpha'}:
        yaml_input = """
        term_name_6:
            type: %s
            pattern: '(a | b)'
        """ % i
        YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


def test_yaml_term_invalid_pattern():
    for i in {'String', 'Alpha'}:
        yaml_input = """
        term_name_6:
            type: %s
            pattern: '(a | b'
        """ % i
        with pytest.raises(ValueError):
            YamlValidation.validate_symbol(yaml.safe_load(yaml_input))


