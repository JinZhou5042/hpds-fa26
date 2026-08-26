/*
Baseline code: Add two arrays and store in a third.
We will use this convention across many benchmark programs:
- SIZE is the logical problem size being computed.
- ITER is the number of times repeated, to yield a useful measurement.
*/

#ifndef SIZE 
#define SIZE 1024*1024
#endif

#ifndef ITER
#define ITER 1000
#endif

#include <x86intrin.h>
#include <sys/time.h>
#include <stdio.h>

double a[SIZE], b[SIZE], c[SIZE];

int main()
{
	/* Initialize the inputs so the computation has a deterministic result. */
	for(int i=0;i<SIZE;i++) {
		a[i] = i * 2;
		b[i] = i / 2;
	}

	/* Mark the start of the experiment. */
	struct timeval start;  
	gettimeofday(&start,0);

	/* Repeat the experiment ITER times. */
	for( int k=0; k<ITER; k++ ) {

		/* Add up each element of the array and multiply by k  */
		for (int i = 0; i < SIZE; i++) {
			c[i] = a[i] + b[i] * k;
		}
	}

	/* Mark the stop of the experiment. */
	struct timeval stop;  
	gettimeofday(&stop,0);

	/* Elapsed is the difference between the two */
	struct timeval elapsed;
	timersub(&stop,&start,&elapsed);

	/* Compute a final checksum of the results. */
	double checksum;
	for(int i=0;i<SIZE;i++) {
		checksum += c[i];
	}
	
	printf("elapsed: %u.%0.6u checksum: %lf\n",elapsed.tv_sec,elapsed.tv_usec,checksum);

	return 0;
}
