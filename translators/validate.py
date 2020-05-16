import sys
import json
import json2python
import input2json
import yaml

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