#!/bin/zsh
set -eu
cd "$(dirname "$0")"
python3 manage.py initdb
exec python3 manage.py runserver 127.0.0.1:8000 --insecure
