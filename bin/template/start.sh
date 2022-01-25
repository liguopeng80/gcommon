#!/bin/bash

WORKING_DIR=$(dirname $0)

export PYTHONPATH=$WORKING_DIR:$WORKING_DIR/src
echo $PYTHONPATH

python src/main.py -c ./deploy/default.yaml



