#!/usr/bin/bash

set -e

SELF=$(readlink -f "$0")
DIR=$(dirname "$SELF")

cd "$DIR"

curl -L https://jsonlogic.com/tests.json -o tests.json

if [[ -e certlogic ]]; then
    rm certlogic/*.json || true
else
    mkdir -p certlogic
fi

curl -L https://github.com/ehn-dcc-development/dgc-business-rules/archive/refs/heads/main.zip -o dgc-business-rules.zip
unzip dgc-business-rules.zip

cp dgc-business-rules-main/certlogic/specification/testSuite/*.json certlogic

rm -r dgc-business-rules-main dgc-business-rules.zip
