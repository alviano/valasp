#!/bin/sh

echo "Utility to create a new environment with the *test* requirements"
echo
echo "Specify the environment name, or type ENTER to use valasp-test"
read name
if [ -z "$name" ]; then
    name="valasp-test"
fi

conda env create --name "$name" --file `dirname $0`/../requirements/test.txt
