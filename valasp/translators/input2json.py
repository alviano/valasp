# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

import json
import shlex
import yaml

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

    @staticmethod
    def __parse_term(term):
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

    @staticmethod
    def __parse_check(check):
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

    @staticmethod
    def __parse_count_sum(current):
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
inclusions = []
ANNOTATION = '@'
ANNOTATION_TERM = ANNOTATION + 'validate_term'
ANNOTATION_ATOM = ANNOTATION + 'validate_atom'
ANNOTATION_SUM = ANNOTATION + 'validate_sum'
ANNOTATION_COUNT = ANNOTATION + 'validate_count'
ANNOTATION_INCLUDE = ANNOTATION + 'include'


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
    if annotation == ANNOTATION_INCLUDE:
        inclusions.extend(elements)
    else:
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


def __validate_include__(current):
    __validate_element__(current, ANNOTATION_INCLUDE)


def __process__(current):
    if current.startswith(ANNOTATION_ATOM):
        __validate_atom__(current)
    elif current.startswith(ANNOTATION_TERM):
        __validate_term__(current)
    elif current.startswith(ANNOTATION_COUNT):
        __validate_count__(current)
    elif current.startswith(ANNOTATION_SUM):
        __validate_sum__(current)
    elif current.startswith(ANNOTATION_INCLUDE):
        __validate_include__(current)


def create_json_structure(filename, file_format):
    if file_format == 'asp':
        return __create_json_from_asp_annotation(filename)
    elif file_format == 'yaml':
        return __create_json_from_yaml(filename)
    else:
        raise ValueError('Unexpected file format %s' % file_format)


def create_json_file(filename, output, file_format):
    my_json = create_json_structure(filename, file_format)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(my_json, f, ensure_ascii=False, indent=4)


def __count_to_dict__(error_message, local_term, atom_name):
    if 'count' in local_term:
        if isinstance(local_term['count'], dict):
            for j in local_term['count']:
                if j != 'min' and j != 'max':
                    raise ValueError("%s Unexpected value for count. Expected min or max" % error_message)
            my = local_term['count']
            my['term'] = atom_name
        elif local_term['count'] != 'int':
            raise ValueError("%s Unexpected value for count. Expected int." % error_message)
        else:
            my = {'term': atom_name}
        return my
    else:
        return None


def __sum_to_dict__(error_message, local_term, atom_name):
    my = {'term': atom_name}
    if 'sum+' in local_term:
        if isinstance(local_term['sum+'], dict):
            for j in local_term['sum+']:
                if j == 'min':
                    my['min_positive'] = local_term['sum+'][j]
                elif j == 'max':
                    my['max_positive'] = local_term['sum+'][j]
                else:
                    raise ValueError("%s Unexpected value for sum+. Expected min or max" % error_message)
        elif local_term['sum+'] != 'int':
            raise ValueError("%s Unexpected value for sum+. Expected int" % error_message)
    if 'sum-' in local_term:
        if isinstance(local_term['sum-'], dict):
            for j in local_term['sum-']:
                if j == 'min':
                    my['min_negative'] = local_term['sum-'][j]
                elif j == 'max':
                    my['max_negative'] = local_term['sum-'][j]
                else:
                    raise ValueError("%s Unexpected value for sum-. Expected min or max" % error_message)
        elif local_term['sum-'] != 'int':
            raise ValueError("%s Unexpected value for sum-. Expected int" % error_message)
    if 'sum+' not in local_term and 'sum-' not in local_term:
        return None
    return my


def __create_json_from_yaml(filename):
    global atoms, inclusions
    atoms = {}
    asp_rules = []
    inclusions = []
    with open(filename, 'r') as f:
        try:
            yaml_input = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)
            return
    my_locals = []
    for j in yaml_input:
        if j.lower() != 'valasp':
            local_terms = []
            local_checks = []
            local_sums = []
            local_counts = []
            local = {'predicate': j, 'terms': local_terms, "checks": local_checks, "sums": local_sums, "counts": local_counts}
            supported_types = {'int', 'str', 'function'}
            local_check = {}
            for i in yaml_input[j]:
                elem = yaml_input[j][i]
                error_message = '[Predicate: %s, Term: %s]' % (j, i)
                if i.lower() != 'asp':
                    local_term = {'name': i}
                    if isinstance(elem, dict):
                        current_type = 'Any'
                        if 'type' in elem:
                            if elem['type'].lower() in supported_types:
                                elem['type'] = elem['type'].lower()
                            current_type = elem['type']
                            if current_type == 'int':
                                supported_elements_int = {'type', 'enum', 'min', 'max', 'sum+', 'sum-', 'count'}
                            elif current_type == 'str' or current_type == 'function':
                                supported_elements_str = {'type', 'enum', 'min_length', 'max_length', 'pattern'}
                            else:
                                current_type = 'custom'
                        for k in elem:
                            if k not in ['sum+', 'sum-', 'count']:
                                if current_type == 'int' and k not in supported_elements_int:
                                    raise ValueError('%s Unexpected keyword %s. Expected one of %s' % (error_message, k, supported_elements_int))
                                elif (current_type == 'str' or current_type == 'function') and k not in supported_elements_str:
                                    raise ValueError('%s Unexpected keyword %s. Expected one of %s' % (error_message, k, supported_elements_str))
                                elif current_type == 'custom' and k != 'type':
                                    raise ValueError('%s Unexpected keyword %s for custom types' % (error_message, k))
                                elif current_type == 'Any' and k != 'type':
                                    raise ValueError('%s Unexpected keyword %s for Any type' % (error_message, k))
                                local_term[k] = elem[k]
                            elif current_type != 'int':
                                raise ValueError('%s Keyword %s is supported only for int' % (error_message, k))
                        local_terms.append(local_term)
                        my_sum = __sum_to_dict__(error_message, elem, i)
                        if my_sum is not None:
                            local_sums.append(my_sum)
                        my_count = __count_to_dict__(error_message, elem, i)
                        if my_count is not None:
                            local_counts.append(my_count)
                    elif isinstance(elem, list):
                        if i.lower() == 'check':
                            for check in elem:
                                for c in check:
                                    my_supported = {'different', 'equals', 'ge', 'gt', 'le', 'lt'}
                                    if c in my_supported and isinstance(check[c], list) and len(check[c]) == 2:
                                        if c not in local_check:
                                            local_check[c] = []
                                        local_check[c].append({'first': check[c][0], 'second': check[c][1]})
                                    else:
                                        if c not in my_supported:
                                            raise ValueError("%s Expected one of: %s" % (error_message, my_supported))
                                        elif not isinstance(check[c], list):
                                            raise ValueError("%s Expected %s to be a list of elements" % (error_message, check[c]))
                                        elif len(check[c]) != 2:
                                            raise ValueError("%s Expected %s to contains two arguments" % (error_message, check[c]))
                        else:
                            raise ValueError("%s Expected keyword check" % error_message)
                    else:
                        if elem.lower() in supported_types:
                            elem = elem.lower()
                        local_term = {'name': i, 'type': elem}
                        local_terms.append(local_term)
                else:
                    asp_rules.append(elem)
            if len(local_check) > 0:
                local_checks.append(local_check)
            my_locals.append(local)
        else:
            for element in yaml_input[j]:
                if element == 'asp':
                    asp_rules.append(yaml_input[j][element])
                elif element == 'include':
                    inclusions = yaml_input[j][element]
                else:
                    raise ValueError("[ValASP] Unexpected keyword %s. Expected asp or include" % element)

    my_json = {'atoms': my_locals, 'rules': asp_rules, 'include': inclusions}
    return my_json


def __create_json_from_asp_annotation(filename):
    global atoms, inclusions
    atoms = {}
    asp_rules = []
    inclusions = []
    with open(filename) as encodingASP:
        lines = encodingASP.readlines()

    for line in lines:
        line = line.strip()
        line = line.lstrip()
        if line.startswith(ANNOTATION):
            __process__(line)
        elif line != '':
            asp_rules.append(line)

    my_json = {'atoms': [], 'rules': asp_rules, 'include': inclusions}
    for i in atoms:
        my_json['atoms'].append(atoms[i].get_root())
    return my_json
