#!/bin/bash

for i in $(seq 0 1000000); do
    bc -l <<< '1+1' > /dev/null
done
