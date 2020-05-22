# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.
import sys


def main():
    if len(sys.argv) != 3:
        print('Usage %s input_file output_file' % sys.argv[0])
        exit(1)

    raise ModuleNotFoundError("currently not implemented")
    # filename = sys.argv[1]
    # with open(filename, 'r') as f:
    #     try:
    #         yaml.safe_load(f)
    #         values = input2json.create_json_structure(filename, 'yaml')
    #     except yaml.YAMLError as exc:
    #         values = input2json.create_json_structure(filename, 'asp')
    #
    # v = json2python.Validation()
    # v.start_validation(values)
    # v.validate()
    # output = v.end_validation()
    #
    # destination = sys.argv[2]
    # with open(destination, 'w', encoding='utf-8') as f:
    #     f.write(output)
