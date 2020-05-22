import re

from valasp.domain.names import PredicateName, AttributeName
from valasp.domain.primitive_types import Integer
from valasp.domain.primitive_types import String
from valasp.domain.primitive_types import Alpha


class YamlValidation:

    @classmethod
    def __validate_keywords(cls, keywords, content, message):
        for c in content:
            if c not in keywords:
                raise ValueError('Unexpected %s in %s' % (c, message))

    @classmethod
    def __validate_predicate_name(cls, content):
        try:
            PredicateName(content)
        except (ValueError, TypeError) as v:
            raise ValueError('%s' % v)

    @classmethod
    def __validate_term_name(cls, content):
        try:
            AttributeName(content)
        except (ValueError, TypeError) as v:
            raise ValueError('%s' % v)

    @classmethod
    def __validate_str(cls, content):
        try:
            String.parse(content)
        except (ValueError, TypeError) as v:
            raise ValueError('%s' % v)

    @classmethod
    def __validate_alpha(cls, content):
        try:
            Alpha.parse(content)
        except (ValueError, TypeError) as v:
            raise ValueError('%s' % v)

    @classmethod
    def __validate_bool(cls, content):
        if not isinstance(content, bool):
            raise ValueError('Unexpected %s. Expected True or False' % content)

    @classmethod
    def __validate_int(cls, content):
        try:
            if isinstance(content, int):
                Integer.parse(str(content))
            else:
                raise ValueError('expected int, but found %s' % type(content))
        except (ValueError, TypeError, OverflowError) as v:
            raise ValueError('%s' % v)

    @classmethod
    def __validate_positive_int(cls, content):
        cls.__validate_int(content)
        c = int(content)
        if c < 0:
            raise ValueError('Expected 0 or a positive integer')

    @classmethod
    def __validate_negative_int(cls, content):
        cls.__validate_int(content)
        c = int(content)
        if c > 0:
            raise ValueError('Expected 0 or a negative integer')

    @classmethod
    def __validate_enum(cls, content, type):
        if not isinstance(content, list):
            raise ValueError('Expected list')
        for c in content:
            try:
                if type == 'Integer':
                    cls.__validate_int(c)
                elif type == 'String':
                    cls.__validate_str(c)
                else:
                    assert type == 'Alpha'
                    cls.__validate_alpha(c)
            except ValueError as v:
                raise ValueError('Invalid value in enum: %s' % v)

    @classmethod
    def __validate_pattern(cls, content):
        try:
            re.compile(content)
        except re.error:
            raise ValueError('Expected regular expression %s ' % re.error)

    @classmethod
    def __validate_min_max(cls, content, positive):
        for c in content:
            try:
                if c == 'min' or c == 'max':
                    if positive:
                        cls.__validate_positive_int(content[c])
                    else:
                        cls.__validate_negative_int(content[c])
            except ValueError as v:
                raise ValueError('%s: %s' % (c, v))
        cls.__validate_min_less_than_max(content)

    @classmethod
    def __validate_min_less_than_max(cls, content):
        if isinstance(content, dict) and 'min' in content and 'max' in content:
            if int(content['min']) >= int(content['max']):
                raise ValueError('min (%s) is expected to be less than max (%s)' % (content['min'], content['max']))

    @classmethod
    def validate_aggregate_sum_pos(cls, content):
        if isinstance(content, dict):
            keywords = {'min', 'max'}
            cls.__validate_keywords(keywords, content, 'sum+')
            cls.__validate_min_max(content, True)
        else:
            if content != 'Integer':
                raise ValueError('Expected keyword Integer')

    @classmethod
    def validate_aggregate_sum_neg(cls, content):
        if isinstance(content, dict):
            keywords = {'min', 'max'}
            cls.__validate_keywords(keywords, content, 'sum-')
            cls.__validate_min_max(content, False)
        else:
            if content != 'Integer':
                raise ValueError('Expected keyword Integer')

    @classmethod
    def validate_aggregate_count(cls, content):
        keywords = {'min', 'max'}
        cls.__validate_keywords(keywords, content, 'count')
        cls.__validate_min_max(content, True)

    @classmethod
    def validate_complex_term_int(cls, content):
        keywords = {'type', 'min', 'max', 'sum+', 'sum-', 'count', 'enum'}
        cls.__validate_keywords(keywords, content, 'Integer type')
        for c in content:
            try:
                if c == 'min' or c == 'max':
                    cls.__validate_int(content[c])
                elif c == 'sum+':
                    cls.validate_aggregate_sum_pos(content[c])
                elif c == 'sum-':
                    cls.validate_aggregate_sum_neg(content[c])
                elif c == 'count':
                    cls.validate_aggregate_count(content[c])
                elif c == 'enum':
                    cls.__validate_enum(content[c], 'Integer')
            except ValueError as v:
                raise ValueError('%s: %s' % (c, v))
        cls.__validate_min_less_than_max(content)

    @classmethod
    def validate_complex_term_string(cls, content):
        keywords = {'type', 'min', 'max', 'pattern', 'count', 'enum'}
        cls.__validate_keywords(keywords, content, 'String type')
        for c in content:
            try:
                if c == 'min' or c == 'max':
                    cls.__validate_positive_int(content[c])
                elif c == 'count':
                    cls.validate_aggregate_count(content[c])
                elif c == 'enum':
                    cls.__validate_enum(content[c], 'String')
                elif c == 'pattern':
                    cls.__validate_pattern(content[c])
            except ValueError as v:
                raise ValueError('%s: %s' % (c, v))
        cls.__validate_min_less_than_max(content)

    @classmethod
    def validate_complex_term_alpha(cls, content):
        keywords = {'type', 'min', 'max', 'pattern', 'count', 'enum'}
        cls.__validate_keywords(keywords, content, 'Alpha type')
        for c in content:
            try:
                if c == 'min' or c == 'max':
                    cls.__validate_positive_int(content[c])
                elif c == 'count':
                    cls.validate_aggregate_count(content[c])
                elif c == 'enum':
                    cls.__validate_enum(content[c], 'Alpha')
                elif c == 'pattern':
                    cls.__validate_pattern(content[c])
            except ValueError as v:
                raise ValueError('%s: %s' % (c, v))
        cls.__validate_min_less_than_max(content)

    @classmethod
    def validate_complex_term_any(cls, content):
        keywords = {'type', 'count'}
        cls.__validate_keywords(keywords, content, 'Any type')
        for c in content:
            try:
                if c == 'count':
                    cls.validate_aggregate_count(content[c])
            except ValueError as v:
                raise ValueError('%s: %s' % (c, v))

    @classmethod
    def validate_complex_term_user_defined(cls, content):
        keywords = {'type', 'count'}
        cls.__validate_keywords(keywords, content, 'user defined symbol')
        for c in content:
            try:
                if c == 'count':
                    cls.validate_aggregate_count(content[c])
            except ValueError as v:
                raise ValueError('%s: %s' % (c, v))

    @classmethod
    def validate_term_type(cls, content):
        keywords = {'Alpha', 'Any', 'Integer', 'String'}
        cls.__validate_str(content)
        if content not in keywords:
            try:
                cls.__validate_term_name(content)
            except ValueError as v:
                raise ValueError('Expected one of %s or user defined symbol: %s' % (keywords, v))

    @classmethod
    def validate_term(cls, content):
        if isinstance(content, dict):
            required = {'type'}
            for r in required:
                if r not in content:
                    raise ValueError('Expected keyword %s' % r)
            try:
                type_ = content['type']
                cls.validate_term_type(type_)
                if type_ == 'Integer':
                    cls.validate_complex_term_int(content)
                elif type_ == 'String':
                    cls.validate_complex_term_string(content)
                elif type_ == 'Alpha':
                    cls.validate_complex_term_alpha(content)
                elif type_ == 'Any':
                    cls.validate_complex_term_any(content)
                else:
                    cls.validate_complex_term_user_defined(content)
            except ValueError as v:
                raise ValueError('%s' % v)
        else:
            cls.validate_term_type(content)

    @classmethod
    def validate_with_fun(cls, content):
        content = str(content)
        keywords = {'FORWARD_IMPLICIT', 'FORWARD', 'IMPLICIT', 'TUPLE'}
        if content not in keywords:
            raise ValueError('Unexpected value %s' % content)

    @classmethod
    def validate_having(cls, content):
        if not isinstance(content, dict):
            raise ValueError('expected structure')
        keywords = {'equals', 'different', 'gt', 'ge', 'lt', 'le'}
        cls.__validate_keywords(keywords, content, 'having')
        for c in content:
            element = content[c]
            if isinstance(element, list):
                for elem in element:
                    if isinstance(elem, list):
                        if len(elem) != 2:
                            raise ValueError(
                                '%s: expected exactly two arguments of the list. Obtained %s' % (c, len(elem)))
                    else:
                        raise ValueError('%s: expected list. Obtained %s' % (c, elem))
            else:
                raise ValueError('expected list. Obtained %s' % element)

    @classmethod
    def validate_valasp_in_symbol(cls, content):
        keywords = {'having', 'is_predicate', 'with_fun', 'auto_blacklist', 'after_init', 'before_grounding',
                    'after_grounding'}
        cls.__validate_keywords(keywords, content, 'valasp of symbol')
        try:
            for c in content:
                if c == 'having':
                    cls.validate_having(content[c])
                if c == 'is_predicate':
                    cls.__validate_bool(content[c])
                if c == 'with_fun':
                    cls.validate_with_fun(content[c])
                if c == 'auto_blacklist':
                    cls.__validate_bool(content[c])
                if c == 'after_init':
                    cls.__validate_str(content[c])
                if c == 'before_grounding':
                    cls.__validate_str(content[c])
                if c == 'after_grounding':
                    cls.__validate_str(content[c])
        except ValueError as v:
            raise ValueError('%s: %s' % (c, v))

    @classmethod
    def validate_symbol(cls, content):
        if not isinstance(content, dict):
            raise ValueError('Expected structure for symbol definition')
        for c in content:
            try:
                if c == 'valasp':
                    cls.validate_valasp_in_symbol(content[c])
                else:
                    cls.__validate_predicate_name(c)
                    cls.validate_term(content[c])
            except ValueError as v:
                raise ValueError('%s: %s' % (c, v))


    @classmethod
    def validate_python(cls, content):
        try:
            cls.__validate_str(content)
        except ValueError as v:
            raise ValueError('%s: %s' % (content, v))

    @classmethod
    def validate_asp(cls, content):
        try:
            cls.__validate_str(content)
        except ValueError as v:
            raise ValueError('%s: %s' % (content, v))

    @classmethod
    def validate_valasp(cls, content):
        keywords = {'python', 'asp'}
        cls.__validate_keywords(keywords, content, 'valasp')
        for c in content:
            try:
                if c == 'python':
                    cls.validate_python(content[c])
                if c == 'asp':
                    cls.validate_asp(content[c])
            except ValueError as v:
                raise ValueError('%s: %s' % (c, v))

    @classmethod
    def validate(cls, content):
        if not isinstance(content, dict):
            raise ValueError('Expected structure')
        try:
            for c in content:
                if c == 'valasp':
                    cls.validate_valasp(content[c])
                else:
                    cls.__validate_predicate_name(c)
                    cls.validate_symbol(content[c])
        except ValueError as v:
            raise ValueError('%s: %s' % (c, v)) from None
