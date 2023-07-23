#!/bin/sh

echo "Specify the environment name, or type ENTER to use valasp"
read name
if [ -z "$name" ]; then
    name="valasp"
fi

conda create --name "$name" python=3.7

conda install --yes --name "$name" pytest=5.4.1
conda install --yes --name "$name" -c potassco clingo=5.4.0
conda install --yes --name "$name" pyyaml=5.3.1
