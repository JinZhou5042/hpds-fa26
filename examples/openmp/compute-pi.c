#include <stdio.h>
#include <math.h>

static long num_steps = 1000;

int main ()
{
	int i;
	double x, pi, sum = 0.0;

	double step = 1.0/(double) num_steps;

	for (i=0; i<num_steps; i++) {
		x = (i+0.5)*step;
		sum = sum + 4.0/(1.0+x*x);
	}
	pi = step * sum;

	printf("computed pi: %.15lf\n",pi);
 	printf("  actual pi: %.15lf\n",M_PI);
	printf("      error: %.15lf\n",M_PI-pi);
}

