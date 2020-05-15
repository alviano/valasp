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
import json
import shlex

supported_checks = {'different', 'equals', 'lt', 'gt', 'le', 'ge'}


class Atom:
    def __init__(self, predicate):
        self.__atom = {}
        self.__predicate = predicate
        self.__terms = []
        self.__checks = []
        self.__atom['predicate'] = self.__predicate
        self.__atom['terms'] = self.__terms
        self.__atom['checks'] = self.__checks
        self.__atom['sums'] = []
        self.__atom['counts'] = []

    def __parse_term(self, term):
        local = {}
        for i in term:
            elements = __split__(i, '=')
            if len(elements) != 2:
                raise ValueError('Wrong syntax while processing %s' % term)
            if not i.startswith('predicate=') and not i.startswith('enum='):
                local['%s' % elements[0]] = '%s' % elements[1]
            if i.startswith('enum'):
                enum_elements = __split__(elements[1], ';')
                local['%s' % elements[0]] = enum_elements

        return local

    def __parse_check(self, check):
        local = {}
        local_check = ''
        for c in check:
            if not c.startswith('predicate='):
                elements = __split__(c, '=')
                if len(elements) != 2:
                    raise ValueError('Wrong syntax while processing %s' % check)
                if elements[0] == 'check' and elements[1] not in supported_checks:
                    raise ValueError('Operation %s not supported' % elements[1])
                if elements[0] == 'check' and elements[1] not in local:
                    local_check = elements[1]
                    local[local_check] = []
        if len(local) == 0:
            return None
        local_map = {}
        for c in check:
            if c.startswith('first=') or c.startswith('second='):
                elements = __split__(c, '=')
                local_map[elements[0]] = elements[1]
        if 'first' not in local_map:
            print('warning: first not defined. Ignored check')
            return None
        if 'second' not in local_map:
            print('warning: second not defined. Ignored check')
            return None
        local[local_check].append(local_map)
        return local

    def __parse_count_sum(self, current):
        local = {}
        for i in current:
            elements = __split__(i, '=')
            if len(elements) != 2:
                raise ValueError('Wrong syntax while processing %s' % current)
            if not i.startswith('predicate=') and not i.startswith('enum='):
                local['%s' % elements[0]] = '%s' % elements[1]
            if i.startswith('enum'):
                enum_elements = __split__(elements[1], ';')
                local['%s' % elements[0]] = enum_elements

        return local

    def add_term(self, term):
        self.__terms.append(self.__parse_term(term))

    def add_sum(self, sum_):
        self.__atom['sums'].append(self.__parse_count_sum(sum_))

    def add_count(self, count_):
        self.__atom['counts'].append(self.__parse_count_sum(count_))

    def add_check(self, check):
        res = self.__parse_check(check)
        if res is not None:
            self.__checks.append(res)

    def get_root(self):
        return self.__atom


atoms = {}
ANNOTATION = '@'
ANNOTATION_TERM = ANNOTATION + 'validate_term'
ANNOTATION_ATOM = ANNOTATION + 'validate_atom'
ANNOTATION_SUM = ANNOTATION + 'validate_sum'
ANNOTATION_COUNT = ANNOTATION + 'validate_count'


def __split__(mystr, c):
    elements = shlex.shlex(mystr, posix=True)
    elements.whitespace += '%s' % c
    elements.whitespace_split = True
    return list(elements)


def __validate_element__(current, annotation):
    current = ''.join(shlex.split(current))
    current = current.replace('\t', '')
    current = current.replace('%s(' % annotation, '')
    current = current.replace(')', '')
    elements = __split__(current, ',')
    for e in elements:
        if e.startswith('predicate='):
            name = e.replace('predicate=', '')
            if name not in atoms:
                atoms[name] = Atom(name)
            if annotation == ANNOTATION_ATOM:
                atoms[name].add_check(elements)
            elif annotation == ANNOTATION_TERM:
                atoms[name].add_term(elements)
            elif annotation == ANNOTATION_SUM:
                atoms[name].add_sum(elements)
            elif annotation == ANNOTATION_COUNT:
                atoms[name].add_count(elements)
            else:
                raise ValueError('Wrong annotation')


def __validate_atom__(current):
    __validate_element__(current, ANNOTATION_ATOM)


def __validate_term__(current):
    __validate_element__(current, ANNOTATION_TERM)


def __validate_count__(current):
    __validate_element__(current, ANNOTATION_COUNT)


def __validate_sum__(current):
    __validate_element__(current, ANNOTATION_SUM)


def __process__(current):
    if current.startswith(ANNOTATION_ATOM):
        __validate_atom__(current)
    elif current.startswith(ANNOTATION_TERM):
        __validate_term__(current)
    elif current.startswith(ANNOTATION_COUNT):
        __validate_count__(current)
    elif current.startswith(ANNOTATION_SUM):
        __validate_sum__(current)


def create_json_structure(filename):
    global atoms
    atoms = {}
    asp_rules = []
    with open(filename) as encodingASP:
        lines = encodingASP.readlines()

    for line in lines:
        line = line.strip()
        line = line.lstrip()
        if line.startswith(ANNOTATION):
            __process__(line)
        elif line != '':
            asp_rules.append(line)

    my_json = {'atoms': [], 'rules': asp_rules}
    for i in atoms:
        my_json['atoms'].append(atoms[i].get_root())
    return my_json


def create_json_file(filename, output):
    my_json = create_json_structure(filename)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(my_json, f, ensure_ascii=False, indent=4)
