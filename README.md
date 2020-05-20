# ValAsp

Validation for Answer Set Programming


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

