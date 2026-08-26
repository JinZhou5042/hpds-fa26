#!/bin/bash

ITER=10000

for (( SIZE=1024; SIZE<1000000; SIZE*=2 ))
do
	g++ -DSIZE=${SIZE} -DITER=${ITER} baseline.c -o baseline -O1
	echo -n "baseline ${SIZE} "
	./baseline
done

for (( SIZE=1024; SIZE<1000000; SIZE*=2 ))
do
        g++ -DSIZE=${SIZE} -DITER=${ITER} improved.c -o improved -O1 -mavx
        echo -n "improved ${SIZE} "
        ./improved
done
