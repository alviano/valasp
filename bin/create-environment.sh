#!/bin/sh

echo "Specify the environment name, or type ENTER to use valasp"
read name
if [ -z "$name" ]; then
    name="valasp"
fi

conda create --name "$name"

conda install --name "$name" pytest
conda install --name "$name" -c potassco clingo
