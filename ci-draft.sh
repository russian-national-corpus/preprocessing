#!/usr/bin/env bash

pylint --rcfile=.pylintrc src

yapf 'src/' --recursive --exclude 'src/Legacy/*' --in-place
