#!/bin/sh

echo "Are you using the correct environment? CTRL+C to abort"
read tmp

conda install --file `dirname $0`/../requirements.txt
