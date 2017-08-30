#!/bin/sh
layers=$1
set -f
IFS=
tri_str=
while [ $((layers-=1)) -ge 0 ]; do
    tri_str=$tri_str╱╲
    printf '%*s\033[4m%s\033[0m\n' $layers '' $tri_str
done
