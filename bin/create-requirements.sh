#!/bin/sh

echo "Utility to create *production* requirements"
echo
echo "Are you using the correct environment? CTRL+C to abort"
read tmp

conda list --export >`dirname $0`/../requirements/prod.conda.txt
