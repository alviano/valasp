import base64
from typing import List

from valasp.domain.names import PredicateName
from valasp.translators.yaml_validation import YamlValidation

INT_MIN = int(-pow(2, 31))
INT_MAX = int(pow(2, 31) - 1)
all_symbols = set()


def _encode(x):
    return base64.b64encode(str(x).encode())


class ErrorMessages:

    @staticmethod
    def raise_error(message, received):
        output = ''
        for r in received:
            output += '{%s}, ' % str(r)
        output = output[:-2]
        error = f"f\"{message}. Received: {output}\""
        return error


class Symbol:

    def __init__(self, content, name):
        self.__name = PredicateName(name)
        self.__terms = []
        self.__valasp = None
        self.__having = []
        self.__is_predicate = True
        self.__with_fun = 'FORWARD_IMPLICIT'
        self.__auto_blacklist = True
        self.__after_init = None
        self.__before_grounding = None
        self.__after_grounding = None
        self.__declaration_content = []
        self.__post_init_content = []
        self.__other_methods_content = []
        self.__parse_content(content)

    def __parse_content(self, content):
        for term_name in content:
            if term_name != 'valasp':
                if isinstance(content[term_name], dict):
                    term_type = content[term_name]['type']
                else:
                    term_type = content[term_name]
                if term_type == 'Integer':
                    term = IntegerTerm(content[term_name], term_name)
                elif term_type == 'String':
                    term = StringTerm(content[term_name], term_name)
                elif term_type == 'Alpha':
                    term = AlphaTerm(content[term_name], term_name)
                elif term_type == 'Any':
                    term = GenericTerm(content[term_name], term_name, 'Any')
                else:
                    if term_type not in all_symbols:
                        raise ValueError('Undefined type %s of %s' % (term_type, term_name))
                    term = UserDefinedTerm(content[term_name], term_name)
                term.set_predicate_name(self.__name)
                self.__terms.append(term)
            else:
                self.__valasp = content[term_name]
        if self.__valasp is not None:
            self.__parse_valasp()

    def __exists_term(self, term_name):
        for i in self.__terms:
            if i.term_name == term_name:
                return True
        return False

    def __parse_valasp(self):
        for c in self.__valasp:
            if c == 'having':
                self.__having = self.__valasp[c]
                self.__parse_having()
            elif c == 'is_predicate':
                self.__is_predicate = self.__valasp[c]
            elif c == 'with_fun':
                self.__with_fun = self.__valasp[c]
            elif c == 'auto_blacklist':
                self.__auto_blacklist = self.__valasp[c]
            elif c == 'after_init':
                self.__after_init = self.__valasp[c]
            elif c == 'before_grounding':
                self.__before_grounding = self.__valasp[c]
            elif c == 'after_grounding':
                self.__after_grounding = self.__valasp[c]
            else:
                assert False

    def __parse_having(self):
        for i in self.__having:
            list_of_comparisons = i.split()
            assert len(list_of_comparisons) == 3
            if not self.__exists_term(list_of_comparisons[0]):
                raise ValueError(f'{self.__name}: having: {i}: {list_of_comparisons[0]} is not a term name')
            if not self.__exists_term(list_of_comparisons[1]):
                raise ValueError(f'{self.__name}: having: {i}: {list_of_comparisons[1]} is not a term name')

    def convert2python(self):
        self.__declaration_content.append(f"@context.valasp(is_predicate={self.__is_predicate}, with_fun=valasp.domain.primitive_types.Fun.{self.__with_fun}, auto_blacklist={self.__auto_blacklist})")
        self.__declaration_content.append(f"class {self.__name.to_class().value}:")
        for term in self.__terms:
            self.__declaration_content.append(f"\t{term.term_name}: {term.term_type}")

        self.__post_init_content.append("\tdef __post_init__(self):")
        for term in self.__terms:
            term.convert2python()
            for i in term.post_init_content:
                self.__post_init_content.append(f"\t\t{i}")

        for having in self.__having:
            comp = having.split()
            assert len(comp) == 3
            self.__post_init_content.append(
                '\t\tif self.%s %s self.%s: raise ValueError("%s")' % (
                    comp[0], comp[1], comp[2], f'Expected {comp[0]} {comp[1]} {comp[2]}'))

        if self.__after_init is not None:
            self.__post_init_content.append(f"\t\t{self.__after_init}")

        for term in self.__terms:
            for i in term.other_methods_content:
                self.__other_methods_content.append(f"\t{i}")

        if self.__before_grounding is not None:
            self.__other_methods_content.append('\t@classmethod')
            self.__other_methods_content.append(f'\tdef before_grounding_{self.__name}(cls):')
            afg = self.__before_grounding.split('\n')
            for j in afg:
                self.__other_methods_content.append('\t\t%s' % j)
        if self.__after_grounding is not None:
            self.__other_methods_content.append('\t@classmethod')
            self.__other_methods_content.append(f'\tdef after_grounding_{self.__name}(cls):')
            afg = self.__after_grounding.split('\n')
            for j in afg:
                self.__other_methods_content.append('\t\t%s' % j)

        output = []
        output.extend(self.__declaration_content)
        if len(self.__post_init_content) > 1:
            output.extend(self.__post_init_content)
        output.extend(self.__other_methods_content)
        return output


class GenericTerm:

    def __init__(self, content, term_name, term_type):
        self.__content = content
        self.term_name = term_name
        self.term_type = term_type
        self.post_init_content = []
        self.other_methods_content = []
        self.predicate_name = ''
        self.__count = None
        if isinstance(content, dict):
            self.__parse_content(content)

    def set_predicate_name(self, predicate_name):
        self.predicate_name = predicate_name

    def __parse_content(self, content):
        if 'count' in content:
            self.__count = content['count']

    def convert2python(self):
        if self.__count is not None:
            self.other_methods_content.append('@classmethod')
            self.other_methods_content.append(
                f'def before_grounding_init_count_{self.term_name}(cls): cls.count_of_{self.term_name} = 0')
            self.other_methods_content.append('@classmethod')
            self.other_methods_content.append(f'def after_grounding_check_count_{self.term_name}(cls):')
            if 'max' in self.__count:
                max_bound = self.__count['max']
                self.other_methods_content.append(f'\tif cls.count_of_{self.term_name} > {max_bound}: raise ValueError(\'count of {self.term_name} in predicate {self.predicate_name} may exceed {max_bound}\')')
            if 'min' in self.__count:
                min_bound = self.__count['min']
                self.other_methods_content.append(f'\tif cls.count_of_{self.term_name} < {min_bound}: raise ValueError(\'count of {self.term_name} in predicate {self.predicate_name} cannot reach {min_bound}\')')
            self.post_init_content.append(f'self.__class__.count_of_{self.term_name} += 1')


class IntegerTerm(GenericTerm):

    def __init__(self, content, term_name):
        GenericTerm.__init__(self, content, term_name, 'Integer')
        self.__min = INT_MIN
        self.__max = INT_MAX
        self.__sum_positive = None
        self.__sum_negative = None
        self.__enum = None
        if isinstance(content, dict):
            self.__parse_content(content)

    def __parse_content(self, content):
        if 'min' in content:
            self.__min = content['min']
        if 'max' in content:
            self.__max = content['max']
        if 'sum+' in content:
            if content['sum+'] != 'Integer':
                self.__sum_positive = content['sum+']
                if 'max' not in content['sum+']:
                    self.__sum_positive['max'] = INT_MAX
            else:
                self.__sum_positive = {'max': INT_MAX}
        if 'sum-' in content:
            if content['sum-'] != 'Integer':
                self.__sum_negative = content['sum-']
                if 'min' not in content['sum-']:
                    self.__sum_positive['min'] = INT_MIN
            else:
                self.__sum_negative = {'min': INT_MIN}
        if 'enum' in content:
            self.__enum = content['enum']

    def __process_sums_positive(self):
        if self.__sum_positive is not None:
            self.other_methods_content.append('@classmethod')
            self.other_methods_content.append(f'def before_grounding_init_positive_sum_{self.term_name}(cls): cls.sum_positive_of_{self.term_name} = 0')
            self.other_methods_content.append('@classmethod')
            self.other_methods_content.append(f'def after_grounding_check_positive_sum_{self.term_name}(cls):')
            if 'max' in self.__sum_positive:
                max_bound = self.__sum_positive['max']
                self.other_methods_content.append(f'\tif cls.sum_positive_of_{self.term_name} > {max_bound}: raise ValueError(\'sum of {self.term_name} in predicate {self.predicate_name} may exceed {max_bound}\')')
            if 'min' in self.__sum_positive:
                min_bound = self.__sum_positive['min']
                self.other_methods_content.append(f'\tif cls.sum_positive_of_{self.term_name} < {min_bound}: raise ValueError(\'sum of {self.term_name} in predicate {self.predicate_name} cannot reach {min_bound}\')')

            self.post_init_content.append(f'if self.{self.term_name} > 0:')
            self.post_init_content.append(f'\tself.__class__.sum_positive_of_{self.term_name} += self.{self.term_name}')

    def __process_sums_negative(self):
        if self.__sum_negative is not None:
            self.other_methods_content.append('@classmethod')
            self.other_methods_content.append(f'def before_grounding_init_negative_sum_{self.term_name}(cls): cls.sum_negative_of_{self.term_name} = 0')
            self.other_methods_content.append('@classmethod')
            self.other_methods_content.append(f'def after_grounding_check_negative_sum_{self.term_name}(cls):')
            if 'max' in self.__sum_negative:
                max_bound = self.__sum_negative['max']
                self.other_methods_content.append(f'\tif cls.sum_negative_of_{self.term_name} > {max_bound}: raise ValueError(\'sum of {self.term_name} in predicate {self.predicate_name} cannot reach {max_bound}\')')
            if 'min' in self.__sum_negative:
                min_bound = self.__sum_negative['min']
                self.other_methods_content.append(f'\tif cls.sum_negative_of_{self.term_name} < {min_bound}: raise ValueError(\'sum of {self.term_name} in predicate {self.predicate_name} may exceed {min_bound}\')')
            self.post_init_content.append(f'if self.{self.term_name} < 0:')
            self.post_init_content.append(f'\tself.__class__.sum_negative_of_{self.term_name} += self.{self.term_name}')

    def convert2python(self):
        if self.__min > INT_MIN:
            message = ErrorMessages.raise_error(f'Should be >= {self.__min}', ['self.%s' % self.term_name])
            self.post_init_content.append(f'if self.{self.term_name} < {self.__min}: raise ValueError({message})')
        if self.__max < INT_MAX:
            message = ErrorMessages.raise_error(f'Should be <= {self.__max}', ['self.%s' % self.term_name])
            self.post_init_content.append(f'if self.{self.term_name} > {self.__max}: raise ValueError({message})')
        if self.__enum is not None:
            s = set(self.__enum)
            message = ErrorMessages.raise_error(f'Should be one of {s}', ['self.%s' % self.term_name])
            self.post_init_content.append(f'if self.{self.term_name} not in {s}: raise ValueError({message})')
        GenericTerm.convert2python(self)
        self.__process_sums_positive()
        self.__process_sums_negative()


class StringAlphaTerm(GenericTerm):

    def __init__(self, content, term_name, term_type):
        GenericTerm.__init__(self, content, term_name, term_type)
        self.__min = 0
        self.__max = INT_MAX
        self.__pattern = None
        self.__enum = None
        if isinstance(content, dict):
            self.__parse_content(content)

    def __parse_content(self, content):
        if 'min' in content:
            self.__min = content['min']
        if 'max' in content:
            self.__max = content['max']
        if 'pattern' in content:
            self.__pattern = content['pattern']
        if 'enum' in content:
            self.__enum = content['enum']

    def convert2python(self):
        if self.__min > 0:
            message = ErrorMessages.raise_error(f'Len should be >= {self.__min}', ['self.%s' % self.term_name])
            self.post_init_content.append(f'if len(self.{self.term_name}) < {self.__min}: raise ValueError({message})')
        if self.__max != INT_MAX:
            message = ErrorMessages.raise_error(f'Len should be <= {self.__max}', ['self.%s' % self.term_name])
            self.post_init_content.append(f'if len(self.{self.term_name}) > {self.__max}: raise ValueError({message})')
        if self.__enum is not None:
            s = set(self.__enum)
            s1 = "{"
            for i in s:
                s1 += f'_({_encode(i)}),'
            s1 = s1[:-1] + "}"

            s2 = ""
            for i in s:
                s2 += '{' + f'_({_encode(i)})' + '},'
            s2 = s2[:-1] + ""
            message = ErrorMessages.raise_error(f'Should be one of [{s2}]', ['self.%s' % self.term_name])
            self.post_init_content.append(f'if self.{self.term_name} not in {s1}: raise ValueError({message})')

        if self.__pattern is not None:
            message = ErrorMessages.raise_error(f'Not match regex {{_({_encode(self.__pattern)})}}', ['self.%s' % self.term_name])
            self.post_init_content.append(f'if not(re.match(_({_encode(self.__pattern)}), self.{self.term_name})): raise ValueError({message})')
        GenericTerm.convert2python(self)


class StringTerm(StringAlphaTerm):
    def __init__(self, content, term_name):
        StringAlphaTerm.__init__(self, content, term_name, 'String')


class AlphaTerm(StringAlphaTerm):
    def __init__(self, content, term_name):
        StringAlphaTerm.__init__(self, content, term_name, 'Alpha')


class UserDefinedTerm(GenericTerm):

    def __init__(self, content, term_name):
        if isinstance(content, dict):
            GenericTerm.__init__(self, content, term_name, PredicateName(content['type']).to_class().value)
        else:
            GenericTerm.__init__(self, content, term_name, PredicateName(content).to_class().value)


class Yaml2Python:

    def __init__(self, content):
        global all_symbols
        all_symbols = set()
        self.__content = content
        self.__valasp_python = ""
        self.__valasp_asp = b''
        self.__valasp_wrap = []
        self.__valasp_max_arity = 16
        self.__symbols = []
        self.__output = []

    def __read_valasp(self):
        if 'valasp' in self.__content:
            if 'python' in self.__content['valasp']:
                self.__valasp_python = self.__content['valasp']['python']
            if 'asp' in self.__content['valasp']:
                self.__valasp_asp = base64.b64encode(str(self.__content['valasp']['asp']).encode())
            if 'wrap' in self.__content['valasp']:
                self.__valasp_wrap = self.__content['valasp']['wrap']
            if 'max_arity' in self.__content['valasp']:
                self.__valasp_max_arity = self.__content['valasp']['max_arity']

    def __read_symbols(self):
        reserved_keywords = {'valasp'}
        for symbol_name in self.__content:
            if symbol_name not in reserved_keywords:
                all_symbols.add(symbol_name)
        for symbol_name in self.__content:
            if symbol_name not in reserved_keywords:
                symbol = Symbol(self.__content[symbol_name], symbol_name)
                self.__symbols.append(symbol)
                self.__output.extend(symbol.convert2python())
                self.__output.append('')

    def convert2python(self) -> List[str]:
        YamlValidation.validate(self.__content)
        self.__read_valasp()
        self.__read_symbols()

        newline = '\n'
        slash_slash = '\\'

        all_import = """
import clingo
import valasp
import valasp.core
import base64
import re
import sys
from valasp.domain.primitive_types import Alpha, Any, Integer, String

def _(x):
    return base64.b64decode(x).decode()
"""
        template = f"""
def main(files, stdout=sys.stdout, stderr=sys.stderr, exit=exit):
    try:
        context = valasp.core.Context(wrap=[{', '.join(self.__valasp_wrap)}], max_arity={self.__valasp_max_arity})

        {f'{newline}        '.join(self.__output)}

        control = clingo.Control()
        for file_ in files:
            control.load(file_)
        try:
            context.valasp_run(
                control, 
                on_validation_done=lambda: print("ALL VALID!{slash_slash}n==========", file=stdout), 
                on_model=lambda m: print(f"Answer: {{m}}{slash_slash}n==========", file=stdout), 
                aux_program=[_({self.__valasp_asp})]
            )
        except RuntimeError as e:
            raise ValueError(context.valasp_extract_error_message(e)) from None
    except Exception as e:
        print('VALIDATION FAILED', file=stderr)
        print('=================', file=stderr)
        print(e, file=stderr)
        print('=================', file=stderr)
"""

        return [all_import, self.__valasp_python, template]
