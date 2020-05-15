"""
Copyright (c) 2020 Mario Alviano and Carmine Dodaro

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""


supported_types = ['int', 'str', 'Any']
__all_types__ = {}
INT_MIN = int(-pow(2, 31))
INT_MAX = int(pow(2, 31)-1)

class ErrorMessages:
    def __init__(self):
        pass

    @staticmethod
    def raise_error(message, received):
        output = ''
        for r in received:
            output += '{%s}, ' % str(r)
        output = output[:-2]
        error = f"f\"{message}. Received: {output}\""
        return error


def __compute_constraints__(check_, validation, mess, received, comparison):
    if mess not in check_:
        return
    element = check_[mess]
    for e in element:
        if 'first' not in e or 'second' not in e:
            continue
        first = e['first']
        second = e['second']
        validation.append(
            'if self._%s_ %s self._%s_: raise ValueError(%s)' % (
                first, comparison, second, ErrorMessages.raise_error('Should be %s' % mess, received)))


def __my_capitalize__(my_str):
    if len(my_str) == 0:
        return ''
    return f'{my_str[0].upper()}{my_str[1:]}'


def __is_integer__(element):
    try:
        v = int(element)
        return True
    except ValueError:
        return False


class Term:
    def __init__(self, term):
        self.__term = term
        self.__term_name = '_%s_' % term['name']
        self.__term_type = term['type']
        self.__output = []
        self.__validation = []

    def get_name(self):
        return self.__term_name

    def get_output(self):
        return self.__output

    def get_validation(self):
        return self.__validation

    def process(self):
        self.__output.append('\t%s: %s' % (self.__term_name, self.__term_type))
        if self.__term['type'] == 'int':
            self.__process_int__()
        elif self.__term['type'] == 'str' or self.__term['type'] == 'function':
            self.__process_str__()
        elif self.__term['type'] == 'Any':
            pass
        elif self.__term['type'] in __all_types__:
            pass
        else:
            raise ValueError("Type not supported")

    def __process_int__(self):
        min_value = INT_MIN
        max_value = INT_MAX
        if 'min_value' in self.__term:
            if __is_integer__(self.__term['min_value']):
                min_value = max(int(self.__term['min_value']), min_value)
            else:
                print('Warning: expected int type for min_value. Ignored.')
        if 'max_value' in self.__term:
            if __is_integer__(self.__term['max_value']):
                max_value = min(int(self.__term['max_value']), max_value)
            else:
                print('Warning: expected int type for max_value. Ignored.')
        message = ErrorMessages.raise_error(f'Should be >= {min_value}', ['self.%s' % self.__term_name])
        self.__validation.append(f'if self.{self.__term_name} < {min_value}: raise ValueError({message})')
        message = ErrorMessages.raise_error(f'Should be <= {max_value}', ['self.%s' % self.__term_name])
        self.__validation.append(f'if self.{self.__term_name} > {max_value}: raise ValueError({message})')
        if 'enum' in self.__term:
            enum = self.__term['enum']
            to_add = []
            for i in enum:
                if __is_integer__(i):
                    to_add.append(i)
                else:
                    print('Warning: expected int type in enum of integers. Ignored.')
            enum_name = '__enum%s_' % self.__term_name
            to_add = ', '.join(to_add)
            self.__validation.append('%s = {%s}' % (enum_name, to_add))
            message = ErrorMessages.raise_error(f'Should be one of {to_add}', ['self.%s' % self.__term_name])
            self.__validation.append(f'if self.{self.__term_name} not in  {enum_name}: raise ValueError({message})')

    def __process_str__(self):
        if 'min_length' in self.__term:
            min_length = self.__term['min_length']
            message = ErrorMessages.raise_error(f'Length should be >= {min_length}', ['self.%s' % self.__term_name])
            self.__validation.append(f'if len(self.{self.__term_name}) < {min_length}: raise ValueError({message})')
        if 'max_length' in self.__term:
            max_length = self.__term['max_length']
            message = ErrorMessages.raise_error(f'Length should be <= {max_length}', ['self.%s' % self.__term_name])
            self.__validation.append(f'if len(self.{self.__term_name}) > {max_length}: raise ValueError({message})')
        if 'pattern' in self.__term:
            pattern = self.__term['pattern']
            message = ErrorMessages.raise_error(f'Input does not match regex \'{pattern}\'',
                                                ['self.%s' % self.__term_name])
            self.__validation.append(f'if not(re.match(\'{pattern}\', self.{self.__term_name})): raise ValueError({message})')
        if 'enum' in self.__term:
            enum = self.__term['enum']
            enum_name = '__enum%s_' % self.__term_name
            to_add = set(enum)
            self.__validation.append('%s = %s' % (enum_name, to_add))
            message = ErrorMessages.raise_error(f'Should be one of {to_add}', ['self.%s' % self.__term_name])
            self.__validation.append(f'if self.{self.__term_name} not in  {enum_name}: raise ValueError({message})')


class Atom:

    def __init__(self, atom):
        self.__atom = atom
        self.__predicate = __my_capitalize__(atom['predicate'])
        self.__terms = atom['terms']
        self.__output = []
        self.__output.append('@validate(context=context)')
        self.__output.append('class %s:' % self.__predicate)
        self.__sums = atom['sums']
        self.__counts = atom['counts']
        self.__all_sums_positive = []
        self.__all_sums_negative = []
        self.__all_counts = []
        self.__post_terms = []

    def get_output(self):
        return self.__output

    def __process_count__(self, validation):
        for i in self.__counts:
            if 'term' in i:
                min_value = INT_MIN
                max_value = INT_MAX
                if 'min' in i:
                    if __is_integer__(i['min']):
                        min_value = max(min_value, int(i['min']))
                if 'max' in i:
                    if __is_integer__(i['max']):
                        max_value = min(max_value, int(i['max']))
                aggregate_name = 'count_of_%s' % (i['term'])
                self.__post_terms.append('%s.%s = 0' % (self.__predicate, aggregate_name))
                self.__all_counts.append((i['term'], aggregate_name, min_value, max_value))
                validation.append('%s.count_of_%s += 1' % (self.__predicate, i['term']))
            else:
                print('Warning: missing term in count')

    def __process_sums__(self, validation):
        for i in self.__sums:
            if 'term' in i:
                min_positive = INT_MIN
                max_positive = INT_MAX
                min_negative = INT_MIN
                max_negative = INT_MAX
                if 'min_positive' in i:
                    if __is_integer__(i['min_positive']):
                        min_positive = max(min_positive, int(i['min_positive']))
                if 'max_positive' in i:
                    if __is_integer__(i['max_positive']):
                        max_positive = min(max_positive, int(i['max_positive']))
                if 'min_negative' in i:
                    if __is_integer__(i['min_negative']):
                        min_negative = max(min_negative, int(i['min_negative']))
                if 'max_negative' in i:
                    if __is_integer__(i['max_negative']):
                        max_negative = min(max_negative, int(i['max_negative']))

                aggregate_name = 'sum_of_%s_pos' % (i['term'])
                self.__post_terms.append('%s.%s = 0' % (self.__predicate, aggregate_name))
                self.__all_sums_positive.append((i['term'], aggregate_name, min_positive, max_positive))
                aggregate_name = 'sum_of_%s_neg' % (i['term'])
                self.__post_terms.append('%s.%s = 0' % (self.__predicate, aggregate_name))
                self.__all_sums_negative.append((i['term'], aggregate_name, min_negative, max_negative))

                validation.append('if self._%s_ >= 0:' % i['term'])
                validation.append('\t%s.sum_of_%s_pos += self._%s_' % (self.__predicate, i['term'], i['term']))
                validation.append('else:')
                validation.append('\t%s.sum_of_%s_neg += self._%s_' % (self.__predicate, i['term'], i['term']))
            else:
                print('Warning: missing term in sum')

    def process(self):
        validation = []
        params = []
        for term in self.__atom['terms']:
            t = Term(term)
            t.process()
            self.__output += t.get_output()
            validation += t.get_validation()
            params.append('self.' + t.get_name())

        for check in self.__atom['checks']:
            if 'equals' in check:
                __compute_constraints__(check, validation, 'equals', params, '!=')
            if 'different' in check:
                __compute_constraints__(check, validation, 'different', params, '==')
            if 'gt' in check:
                __compute_constraints__(check, validation, 'gt', params, '<=')
            if 'lt' in check:
                __compute_constraints__(check, validation, 'lt', params, '>=')
            if 'ge' in check:
                __compute_constraints__(check, validation, 'ge', params, '<')
            if 'le' in check:
                __compute_constraints__(check, validation, 'le', params, '>')

        self.__process_sums__(validation)
        self.__process_count__(validation)

        self.__output.append('\t@classmethod')
        self.__output.append('\tdef check(cls):')
        if len(self.__all_sums_positive) + len(self.__all_sums_negative) + len(self.__all_counts) > 0:
            for j in self.__all_sums_positive:
                (t_name, name, min_value, max_value) = j
                if min_value > INT_MIN:
                    self.__output.append('\t\tif cls.%s < %s: raise ValueError(f\'sum of %s cannot reach %s\')' % (name, min_value, t_name, min_value))
                self.__output.append('\t\tif cls.%s > %s: raise ValueError(f\'sum of %s may exceed %s\')' % (name, max_value, t_name, max_value))
            for j in self.__all_sums_negative:
                (t_name, name, min_value, max_value) = j
                self.__output.append('\t\tif cls.%s < %s: raise ValueError(f\'sum of %s may exceed %s\')' % (name, min_value, t_name, min_value))
                if max_value < INT_MAX:
                    self.__output.append('\t\tif cls.%s > %s: raise ValueError(f\'sum of %s cannot reach %s\')' % (name, max_value, t_name, max_value))
            for j in self.__all_counts:
                (t_name, name, min_value, max_value) = j
                if min_value > INT_MIN:
                    self.__output.append('\t\tif cls.%s < %s: raise ValueError(f\'count of %s cannot reach than %s\')' % (name, min_value, t_name, min_value))
                self.__output.append('\t\tif cls.%s > %s: raise ValueError(f\'count of %s may exceed than %s\')' % (name, max_value, t_name, max_value))
        else:
            self.__output.append('\t\tpass')

        self.__output.append('\tdef __post_init__(self):')
        if len(validation) == 0:
            self.__output.append('\t\tpass')
        else:
            for v in validation:
                self.__output.append('\t\t%s' % v)
        self.__output.append('')
        self.__output.extend(self.__post_terms)

class Output:

    def __init__(self, output, rules):
        self.__template = f'#script(python).\n\n' \
                          f'import clingo\n' \
                          f'import re\n' \
                          f'from valasp import Context, validate\n' \
                          f'from typing import Callable\n\n\n' \
                          f'context = Context()\n' \
                          f'{output}\n\n' \
                          f'def main(prg):\n' \
                          f'\tcontext.run(prg)\n' \
                          f'#end.\n' \
                          f'{rules}\n'

    def get_output(self):
        return self.__template


class Validation:
    def __init__(self):
        self.__output = []
        self.__atoms = None
        self.__rules = []

    def start_validation(self, atoms, rules):
        self.__atoms = atoms
        self.__rules = rules
        for atom in atoms:
            for term in atom['terms']:
                if 'type' not in term:
                    term['type'] = 'Any'
                if term['type'] not in supported_types:
                    term['type'] = __my_capitalize__(term['type'])
                    term['type'] = '%s' % term['type']
                    __all_types__[term['type']] = 1

    def validate(self):
        if self.__atoms is None:
            print('Start validation must be called')
            return

        for atom in self.__atoms:
            a = Atom(atom)
            a.process()
            self.__output += a.get_output()

    def end_validation(self):
        output = Output('\n'.join(self.__output), '\n'.join(self.__rules))
        return output.get_output()
