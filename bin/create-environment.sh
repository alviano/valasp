#!/bin/sh

echo "Specify the environment name, or type ENTER to use valasp"
read name
if [ -z "$name" ]; then
    name="valasp"
fi

conda env create --name "$name" --file `dirname $0`/../requirements.txt
