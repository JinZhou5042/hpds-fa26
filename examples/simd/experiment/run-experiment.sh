#!/bin/bash

ITER=1000000

for (( SIZE=1024; SIZE<10000; SIZE*=2 ))
do
	g++ -DSIZE=${SIZE} -DITER=${ITER} baseline.c -o baseline -O0
	echo -n "baseline ${SIZE} "
	./baseline
done

for (( SIZE=1024; SIZE<10000; SIZE*=2 ))
do
        g++ -DSIZE=${SIZE} -DITER=${ITER} improved.c -o improved -O0 -mavx
        echo -n "improved ${SIZE} "
        ./improved
done




