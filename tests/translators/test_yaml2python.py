import base64
import pytest
import yaml

from valasp.translators.yaml2python import Symbol, IntegerTerm, Yaml2Python

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


def test_symbol_type_valasp():
    for i in {'FORWARD_IMPLICIT', 'FORWARD', 'IMPLICIT', 'TUPLE'}:
        yaml_input = """
        predicate:
            value: Integer
            valasp:
                is_predicate: False
                auto_blacklist: False
                with_fun: %s
                before_grounding: cls.a = 0
                after_grounding: print(cls.a)
        """ % i
        result = yaml.safe_load(yaml_input)
        obj = Symbol(result["predicate"], "predicate")
        output = obj.convert2python()
        assert "@context.valasp(is_predicate=False, with_fun=valasp.domain.primitive_types.Fun.%s, auto_blacklist=False)" % i in output
        assert "\tvalue: Integer" in output
        assert "\tdef __post_init__(self):" not in output
        assert "\tdef after_grounding_predicate(cls):" in output
        assert "\t\tcls.a = 0" in output
        assert "\t\tprint(cls.a)" in output


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


def test_symbol_min_max_integer():
    yaml_input = """
    value:
        type: Integer
        min: 10   
        max: 100
    """
    result = yaml.safe_load(yaml_input)
    obj = IntegerTerm(result["value"], "value")
    obj.convert2python()
    found_element = False
    for i in obj.post_init_content:
        if i.startswith("if self.value < 10: raise ValueError"):
            found_element = True
    assert found_element
    found_element = False
    for i in obj.post_init_content:
        if i.startswith("if self.value > 100: raise ValueError"):
            found_element = True
    assert found_element


def test_symbol_enum_integer():
    yaml_input = """
    value:
        type: Integer
        enum: [1, 2, 3]
    """
    result = yaml.safe_load(yaml_input)
    obj = IntegerTerm(result["value"], "value")
    obj.convert2python()
    found_element = False
    for i in obj.post_init_content:
        if i.startswith("if self.value not in {1, 2, 3}: raise ValueError"):
            found_element = True
    assert found_element


def test_symbol_min_max():
    for i in {'String', 'Alpha'}:
        yaml_input = """
        predicate:
            value:
                type: %s
                min: 10   
                max: 100
        """ % i
        result = yaml.safe_load(yaml_input)
        obj = Symbol(result["predicate"], "predicate")
        output = obj.convert2python()
        assert "class Predicate:" in output
        assert "\tvalue: %s" % i in output
        assert "\tdef __post_init__(self):" in output
        found_element = False
        for i in output:
            if i.startswith("\t\tif len(self.value) < 10: raise ValueError"):
                found_element = True
        assert found_element
        found_element = False
        for i in output:
            if i.startswith("\t\tif len(self.value) > 100: raise ValueError"):
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


def test_symbol_sum_positive_default():
    yaml_input = """
    predicate:
        value:
            type: Integer
            sum+: Integer                
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
    assert "\t\tif cls.sum_positive_of_value > 2147483647: raise ValueError('sum of value in predicate predicate may exceed 2147483647')" in output


def test_symbol_sum_positive_missing_max():
    yaml_input = """
    predicate:
        value:
            type: Integer
            sum+:
                min: 10                
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
    assert "\t\tif cls.sum_positive_of_value > 2147483647: raise ValueError('sum of value in predicate predicate may exceed 2147483647')" in output
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


def test_symbol_sum_negative_default():
    yaml_input = """
    predicate:
        value:
            type: Integer
            sum-: Integer
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
    assert "\t\tif cls.sum_negative_of_value < -2147483648: raise ValueError('sum of value in predicate predicate may exceed -2147483648')" in output


def test_symbol_sum_negative_missing_min():
    yaml_input = """
    predicate:
        value:
            type: Integer
            sum-:
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
    assert "\t\tif cls.sum_negative_of_value < -2147483648: raise ValueError('sum of value in predicate predicate may exceed -2147483648')" in output
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
        for oper in {"==", "!=", ">", ">=", "<", "<=", " == ", " !=", "> ", "  >=", "<  ", "  <=  "}:
            yaml_input = """
             predicate:
                 first: %s
                 second: %s
                 valasp:
                     having:
                        - first%ssecond                  
             """ % (i, i, oper)
            result = yaml.safe_load(yaml_input)
            obj = Symbol(result["predicate"], "predicate")
            output = obj.convert2python()
            assert "class Predicate:" in output
            assert "\tfirst: %s" % i in output
            assert "\tsecond: %s" % i in output
            assert "\tdef __post_init__(self):" in output
            oper = oper.lstrip().rstrip()
            assert "\t\tif self.first %s self.second: raise ValueError(\"Expected first %s second\")" % (oper, oper) in output


def test_symbol_pattern():
    for a in {'String', 'Alpha'}:
        yaml_input = """
        predicate:
            value:
                type: %s
                pattern: a|b
        """ % a
        result = yaml.safe_load(yaml_input)
        obj = Symbol(result["predicate"], "predicate")
        output = obj.convert2python()
        assert "class Predicate:" in output
        assert "\tvalue: %s" % a in output
        assert "\tdef __post_init__(self):" in output
        found_element = False
        for i in output:
            if i.startswith("\t\tif not(re.match(_(%s), self.value)):" % base64.b64encode(str("a|b").encode())):
                found_element = True
        assert found_element


def test_missing_type():
    yaml_input = f"""
        year:
            value:
                type: Integer
                min: 1900
                max: 2100

        date:
            year: year
            month:
                type: Integer
                min: 1
                max: 12
            day: day
    """
    result = yaml.safe_load(yaml_input)
    with pytest.raises(ValueError) as error:
        Yaml2Python(result).convert2python()
    assert 'Undefined type' in str(error.value)


def test_missing_field_in_having_right():
    yaml_input = f"""
        ordered_pair:
            first: Integer
            second: Integer
            valasp:
                having:
                    - first < secnd
    """
    result = yaml.safe_load(yaml_input)
    with pytest.raises(ValueError) as error:
        Yaml2Python(result).convert2python()
    assert 'secnd is not a term name' in str(error.value)


def test_missing_field_in_having_left():
    yaml_input = f"""
            ordered_pair:
                first: Integer
                second: Integer
                valasp:
                    having:
                        - secnd > first
        """
    result = yaml.safe_load(yaml_input)
    with pytest.raises(ValueError) as error:
        Symbol(result["ordered_pair"], "ordered_pair")
    assert 'secnd is not a term name' in str(error.value)


def test_user_defined_term():
    yaml_input = f"""
        pred:
            value: Integer
        
        predicate:
            term:
               type: pred
               count:
                    min: 10
    """
    result = yaml.safe_load(yaml_input)
    lines = Yaml2Python(result).convert2python()
    assert 'term: Pred' in '\n'.join(lines)
