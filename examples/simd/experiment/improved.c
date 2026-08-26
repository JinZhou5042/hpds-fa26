/*
Improved code: Use SIMD intrinsics to process the array more efficiently.
*/

#ifndef SIZE 
#define SIZE 1024*1024
#endif

#ifndef ITER
#define ITER 1000
#endif

#include <x86intrin.h>
#include <bits/stdc++.h>
#include <sys/time.h>

using namespace std;

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

		/* Broadcast K into ks */
		double kd = k;
		__m256d ks = _mm256_broadcast_sd(&kd);

		/* For each element of the array (step by 4) */
		for (int i = 0; i < SIZE; i += 4) {

			/* Load four values from a and b */
			__m256d as = _mm256_loadu_pd(&a[i]);
			__m256d bs = _mm256_loadu_pd(&b[i]);

			/* Mulitply the bs by ks */
			bs = _mm256_mul_pd(bs,ks);

			/* Add four sets of values */
		    	__m256d cs = _mm256_add_pd(as,bs);

			/* Store four values back into c. */
			_mm256_storeu_pd(&c[i],cs);
		}
	}

	/* Mark the stop of the experiment. */
	struct timeval stop;  
	gettimeofday(&stop,0);

	/* Elapsed is the difference between the two */
	struct timeval elapsed;
	timersub(&stop,&start,&elapsed);
	
	/* Sum up the values of the array to get an overall result. */
	/* This value should stay the same for each run. */

	double checksum = 0.0;
	for(int i=0;i<SIZE;i++) {
		checksum += c[i];
	}

	printf("elapsed: %u.%0.6u checksum: %lf\n",elapsed.tv_sec,elapsed.tv_usec,checksum);

	return 0;
}
