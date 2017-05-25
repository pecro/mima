#!/bin/bash
loop=$1
delay=1

for i in $(seq 1 $loop); do
    sleep $delay
    fortune
    echo '-------------------------------------------------'
done
         
