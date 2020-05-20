#!/bin/sh

echo "Specify the environment name, or type ENTER to use valasp"
read name
if [ -z "$name" ]; then
    name="valasp"
fi

conda create --name "$name" python=3.7

conda install --yes --name "$name" pytest
conda install --yes --name "$name" -c potassco clingo
conda install --yes --name "$name" pyyaml
