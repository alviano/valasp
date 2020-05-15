import sys
import json
import json2python
import asp2json

if len(sys.argv) != 2:
    raise AssertionError('Expected file with annotations')

filename = sys.argv[1]

values = asp2json.create_json_structure(filename)

atoms = values['atoms']
rules = values['rules']
v = json2python.Validation()
v.start_validation(atoms, rules)
v.validate()
output = v.end_validation()
print(output)

# asp2json.create_json_file(filename, 'output.json')