#!/bin/sh

echo "Utility to create *test* requirements"
echo
echo "Are you using the correct environment? CTRL+C to abort"
read tmp


tmpfile=$(mktemp /tmp/valasp.XXXXXX)
conda list --export >"$tmpfile"
diff --new-line-format="" --unchanged-line-format="" \
    "$tmpfile" \
    `dirname $0`/../requirements/prod.conda.txt \
    >`dirname $0`/../requirements/test.conda.txt
rm "$tmpfile"

