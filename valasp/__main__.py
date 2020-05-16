#!/usr/bin/env python3

# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

import sys
import yaml

from valasp.translators import input2json, json2python

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage %s input_file output_file' % sys.argv[0])
        exit(1)

    filename = sys.argv[1]
    values = None
    with open(filename, 'r') as f:
        try:
            yaml.safe_load(f)
            values = input2json.create_json_structure(filename, 'yaml')
        except yaml.YAMLError as exc:
            values = input2json.create_json_structure(filename, 'asp')

    v = json2python.Validation()
    v.start_validation(values)
    v.validate()
    output = v.end_validation()

    destination = sys.argv[2]
    with open(destination, 'w', encoding='utf-8') as f:
        f.write(output)
