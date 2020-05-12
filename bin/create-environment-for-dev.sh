#!/bin/sh

echo "Utility to create a new environment with the *dev* requirements"
echo
echo "Specify the environment name, or type ENTER to use valasp-dev"
read name
if [ -z "$name" ]; then
    name="valasp-dev"
fi

conda env create --name "$name" --file `dirname $0`/../requirements/dev.txt
