#!/bin/bash
loop=$1
delay=0.5

for i in $(seq 1 $loop); do
    sleep $delay
    output=$(fortune)
    echo "$output"
    echo "$output" 1>&2
    echo '-------------------------------------------------'
    echo '-------------------------------------------------' 1>&2
done
         
