/*
Example program that computes one-dimensional kinematics on a set of bodies.
This version defines each body as a structure, and then makes an array of structures.
Compare this to the alternate approach in structure-of-arrays.c
*/

#include <cstdio>

#ifndef SIZE
#define SIZE 1024*1024
#endif

#ifndef ITER
#define ITER 1000
#endif

/*
Consider a Newtownian body, described by a position (m),
velocity (m/s), acceleration (m/s^2) and mass (kg)
*/

struct body {
	double position;
	double velocity;
	double accel;
	double mass;       
};

/* Now let there be SIZE bodies total. */

struct body b[SIZE];

int main()
{
	double force = 3.2;    // constant force applied to each body
	double deltat = 0.01;  // compute time intervals of 1/100 s

	/* Give every body a finite, nonzero mass. */
	for(int i=0;i<SIZE;i++) {
		b[i].mass = 1.0 + (i % 100) * 0.01;
	}

	/* Repeat the computation ITER times... */
	for(int k=0;k<ITER;k++) {

		/* Update each body in the array... */
		for(int i=0;i<SIZE;i++) {

			b[i].accel = force / b[i].mass;
			b[i].velocity = b[i].accel * deltat;
			b[i].position += b[i].velocity * deltat;
		}
	}

	double checksum = 0.0;
	for(int i=0;i<SIZE;i++)
		checksum += b[i].position;

	std::printf("checksum: %.6f\n", checksum);
	return 0;
}
