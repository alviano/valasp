# VALASP

Validation for Answer Set Programming by specification rules written in YAML or Python.
Details on the usage are given in the online documentation: https://alviano.github.io/valasp.
A taste is given in the [usage](#usage) section.



## Setup

Obtain a local copy of the repository:

```shell script
$ git clone git@github.com:alviano/valasp.git
$ cd valasp
``` 


Execute the following script to create a conda environment with all dependencies:

```shell script
$ ./bin/create-environment.sh
```


Don't forget to activate the environment with

```shell script
$ conda activate valasp
``` 

where `valasp` is the name given to the virtual environment.


To install `valasp` as a pip module, use the following command:

```shell script
$ pip install -e .
```


To run all tests, use the following command:

```shell script
$ pytest
```


## Usage

Activate the environment with

```shell script
$ conda activate valasp
``` 

where `valasp` is the name given to the virtual environment.
Let's try to validate `examples/bday.invalid.asp` against the specification given in `examples/bday.yaml`: 

```shell script
(valasp) $ python -m valasp examples/bday.yaml examples/bday.invalid.asp 
VALIDATION FAILED
=================
Invalid instance of bday:
    in constructor of bday
    in constructor of date
  with error: expecting arity 3 for TUPLE, but found 2; invalid term (1982,123) in atom bday(bigel,(1982,123))
=================
```

We are pointed to an invalid term in an invalid atom.
If `valasp` is used at coding time, it is likely that this minimal information will drive you to quickly identify the origin of the problem.
The content of the two files is the following: 

```shell script
(valasp) $ cat examples/bday.yaml
valasp:
    python: |+
        import datetime

date:
    year: Integer
    month: Integer
    day: Integer    

    valasp:
        is_predicate: False
        with_fun: TUPLE
        after_init: |+
            datetime.datetime(self.year, self.month, self.day)

bday:
    name: Alpha
    date: date
    
(valasp) $ cat examples/bday.invalid.asp 
bday(sofia, (2019,6,25)).
bday(leonardo, (2018,2,1)).
bday(bigel, (1982,123)).
```

## Documentation

The documentation is available online at https://alviano.github.io/valasp.

The documentation is produced with `sphinx`, which can be added to the virtual environment with the following command:

```shell script
$ conda install sphinx
```

To produce a local copy of the documentation, run the following commands:

```shell script
$ cd docs
$ make generate
$ make html
```

The HTML documentation can then be found in `docs/builds/html/index.html`.


## Copyright

Copyright 2020 Mario Alviano and Carmine Dodaro

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
