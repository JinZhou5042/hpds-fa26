/*
Example program that computes one-dimensional kinematics on a set of bodies.
This version is DIFFERENT because it groups together each type of value into a single array.
Compare this to array-of-structures.c
*/

#include <cstdio>

#ifndef SIZE
#define SIZE 1024*1024
#endif

#ifndef ITER
#define ITER 1000
#endif

/*
Consider SIZE Newtonian bodies, each with position(m),
velocity (m/s), acceleration (m/s^2), and mass (kg)
*/

struct body {
	double position[SIZE];
	double velocity[SIZE];
	double accel[SIZE];
	double mass[SIZE];
};

/* Now let there be *one* structure containing everything */

struct body b;

int main()
{
	double force = 3.2;    // constant force applied to each body
	double deltat = 0.01;  // compute time intervals of 1/100 s

	/* Give every body a finite, nonzero mass. */
	for(int i=0;i<SIZE;i++) {
		b.mass[i] = 1.0 + (i % 100) * 0.01;
	}

	/* Repeat the computation ITER times... */
	for(int k=0;k<ITER;k++) {

		/* Update each body in the array... */
		for(int i=0;i<SIZE;i++) {
		  
			b.accel[i] = force / b.mass[i];
			b.velocity[i] = b.accel[i] * deltat;
			b.position[i] += b.velocity[i] * deltat;
		}
	}

	double checksum = 0.0;
	for(int i=0;i<SIZE;i++)
		checksum += b.position[i];

	std::printf("checksum: %.6f\n", checksum);
	return 0;
}
