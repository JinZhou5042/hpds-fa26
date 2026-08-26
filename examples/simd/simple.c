/*
Example from Chapter 10.1 of Algorithmica / HPC by Sergey Slotin
Just sum up all the values of the array.
Try compiling this in various ways to show impact of SIMD:
   g++ simple.c -o simple -O0
   g++ simple.c -o simple -O3 -mavx
   ...
*/ 

#include <cstdio>

const int n = 1e5;
int a[n], s = 0;

int main() {
    for (int i = 0; i < n; i++)
        a[i] = (i % 3) - 1;

    for (int t = 0; t < 10000; t++)
        for (int i = 0; i < n; i++)
            s += a[i];

    std::printf("checksum: %d\n", s);
    return 0;
}
