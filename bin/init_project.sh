#!/usr/bin/env bash

mkdir deploy
touch deploy/default.yaml
touch deploy/example.secret.default.yaml

mkdir docs
touch docs/README.md

mkdir data
touch data/README.md

mkdir log
touch log/README.md

mkdir bin
touch bin/README.md

cp src/gcommon/.gitignore ./
