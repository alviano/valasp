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


supported_types = ['int', 'str']
__all_types__ = {}

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
        elif self.__term['type'] in __all_types__:
            pass
        else:
            raise ValueError("Type not supported")

    def __process_int__(self):
        min_value = int(-pow(2, 31))
        max_value = int(pow(2, 31) - 1)
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

    def get_output(self):
        return self.__output

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

        self.__output.append('\tdef __post_init__(self):')
        if len(validation) == 0:
            self.__output.append('\t\tpass')
        else:
            for v in validation:
                self.__output.append('\t\t%s' % v)
        self.__output.append('')


class Output:

    def __init__(self, output):
        self.__template = f'#script(python).\n\n' \
                          f'import clingo\n' \
                          f'import re\n' \
                          f'from valasp import Context, validate\n' \
                          f'from typing import Callable\n\n\n' \
                          f'context = Context()\n' \
                          f'{output}\n\n' \
                          f'def main(prg):\n' \
                          f'\tprg.add("validators", [], context.validators())\n' \
                          f'\tprg.ground([\n' \
                          f'\t("base", []),\n' \
                          f'\t("validators", []),\n' \
                          f'\t], context=context)\n' \
                          f'\tprg.solve()\n' \
                          f'#end.\n'

    def get_output(self):
        return self.__template


class Validation:
    def __init__(self):
        self.__output = []
        self.__atoms = None

    def start_validation(self, atoms):
        self.__atoms = atoms
        for atom in atoms:
            for term in atom['terms']:
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
        output = Output('\n'.join(self.__output))
        return output.get_output()