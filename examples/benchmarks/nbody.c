#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <sys/time.h>

#ifndef SIZE
#define SIZE 100
#endif

#ifndef ITER
#define ITER 10000
#endif

#define G 10000000

/*
NOTE: I have deliberately taken an "unsophisticated" approach
to setting up these structures.  You are welcome to extend
to three dimensions, rewrite using C++ vectors, rearrange
the memory layout, or whatever else makes you happy or
improves the performance.  Go nuts.
*/

/* Define the properties of a Newtonian body. */

struct body {
	double x,y;	// position in two dimensions
	double vx,vy;	// velocity (m/s) in two dimensions
	double ax,ay;	// acceleration (m/s^2) in two dimensions
	double mass;	// mass (kg)
};

struct body B[SIZE];
double deltat = 0.01;

/* Initialize one body with a random location, velocity, mass, and zero accel. */

void nbody_init( struct body *b )
{
	b->x = rand()%1000;
	b->y = rand()%1000;

	b->vx = rand()%200-100.0;
	b->vy = rand()%200-100.0;

	b->ax = 0;
	b->ay = 0;

	b->mass = (1+rand()%10) / 1000.0;
}

/* Display the position of all bodies in an array. */

void nbody_print_all( struct body B[] )
{
	for(int i=0;i<SIZE;i++) {
		printf("%0.2lf %0.2lf ",B[i].x,B[i].y);
	}
	printf("\n");
}

/* Set acceleration to zero at the start of an iteration. */

void nbody_zero_accel( struct body *b )
{
	b->ax = b->ay = 0;
}

/* Kernel: cause to bodies to interact via gravitational force. */

void nbody_interact( struct body *a, struct body *b )
{
	/* Special case: a body cannot interact with itself. */
	if(a==b) return;
  
	/* First determine the triangle distance between. */
	double dx = b->x - a->x;
	double dy = b->y - a->y;
	double r = sqrt( dx*dx + dy*dy );

	/* If two bodies collide, reverse velocities. */
	if(r<1.0) {
		a->vx = -a->vx;
		a->vy = -a->vy;
		b->vx = -b->vx;
		b->vy = -b->vy;
	}

	/* Newton's law of gravitation */
	double force = (G * a->mass * b->mass) / (r*r) ;
	
	/* Separate the components of the force in two dimensions */
	double xforce = force * dx / r;
	double yforce = force * dy / r;

	/* Apply Newton's second law to object a */
	a->ax += xforce / a->mass;
	a->ay += yforce / a->mass;

	/* And then to object b (opposite direction) */
	b->ax -= xforce / b->mass;
	b->ay -= yforce / b->mass;
}

/* Apply the total acceleration to velocity and position. */

void nbody_move( struct body *b, double deltat )
{
	b->vx += b->ax * deltat;
	b->vy += b->ay * deltat;

	b->x += b->vx * deltat;
	b->y += b->vy * deltat;
}

/* Advance the simulation by one timestep. */
    
void nbody_timestep()
{
	/* Reset total acceleration to zero. */ 

	for(int i=0; i<SIZE; i++) {
		nbody_zero_accel(&B[i]);
	}

	/* For each pair of bodies, compute force interactions. */
	
	for(int i=0; i<SIZE; i++) {
		for(int j=0; j<SIZE; j++) {
			if(i==j) continue;
			nbody_interact(&B[i],&B[j]);
		}
	}

	/* Move each body according to accumulated acceleration. */
	
	for(int i=0; i<SIZE; i++) {
		nbody_move(&B[i],deltat);
	}
}

/* Add up the positions of all the objects as a correctness check */

double nbody_addup( struct body B[] )
{
  double total = 0;
  for(int i=0;i<SIZE;i++) {
    total += B[i].x + B[i].y;
  }
  return total;
}

int main( int argc, char *argv[] )
{
	srand(7);
  
	int i;
  
	for(i=0;i<SIZE;i++) {
		nbody_init(&B[i]);
	}
	
	/* Mark the start of the experiment. */
	struct timeval start;  
	gettimeofday(&start,0);

	for(int k=0; k<ITER; k++) {
		nbody_timestep();
		
		if(i%1000==0) nbody_print_all(B);
	}

	/* Mark the stop of the experiment. */
	struct timeval stop;  
	gettimeofday(&stop,0);

	/* Elapsed is the difference between the two */
	struct timeval elapsed;
	timersub(&stop,&start,&elapsed);

	/* Compute a final checksum of the results. */
	double checksum = nbody_addup(B);

	printf("elapsed: %u.%0.6u checksum: %lf\n",elapsed.tv_sec,elapsed.tv_usec,checksum);

	return 0;
}
