/*
Perform a simple computation using gcc SIMD intrinsics directly.

We will use this convention across many benchmark programs:
SIZE is the logical problem size being computed.
ITER is the number of times repeated, to yield a useful measurement.
*/

#ifndef SIZE 
#define SIZE 1024*1024
#endif

#ifndef ITER
#define ITER 100000
#endif

#include <x86intrin.h>
#include <bits/stdc++.h>

using namespace std;

double a[SIZE], b[SIZE], c[SIZE];

int main()
{
	/* Repeat the experiment ITER times. */
	for( int k=0; k<ITER; k++ ) {

		/* For each element of the array (step by 4) */
		for (int i = 0; i < SIZE; i += 4) {

			/* Load four elements of each array */
			__m256d x = _mm256_loadu_pd(&a[i]);
			__m256d y = _mm256_loadu_pd(&b[i]);

			/* Add four sets of values */
		    	__m256d z = _mm256_add_pd(x, y);

			/* Store four values into memory, starting at c[i] */
		    	_mm256_storeu_pd(&c[i], z);
		}
	}

	return a[0];
}

