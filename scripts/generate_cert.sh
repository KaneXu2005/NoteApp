#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p nginx/certs
if [ -e nginx/certs/notesapp.key ] || [ -e nginx/certs/notesapp.crt ]; then
    echo 'Certificate/key already exist; refusing to overwrite them.' >&2
    exit 1
fi
umask 077
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/certs/notesapp.key -out nginx/certs/notesapp.crt \
    -config nginx/localhost.cnf
