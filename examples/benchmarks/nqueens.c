#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <sys/time.h>

#ifndef SIZE
#define SIZE 14
#endif

int total_solutions = 0;
int max_solutions_printed = 16;

int any_in_same_column( int queenxpos[SIZE], int xpos, int ypos )
{
	for(int j=0;j<ypos;j++) {
		if(queenxpos[j]==xpos) return 1;
	}	

	return 0;
}

int any_in_same_diagonal( int queenxpos[SIZE], int xpos, int ypos )
{
	for(int j=0;j<ypos;j++) {
		int xdist = xpos - queenxpos[j];
	  	int ydist = ypos - j;

		if(xdist<0) xdist=-xdist;
		
		if(xdist==ydist) return 1;
	}	

	return 0;
}

void nqueens_print( int queenxpos[SIZE] )
{
	if(total_solutions<max_solutions_printed) {
		printf("solution %d: ",total_solutions);
		for(int j=0;j<SIZE;j++) {
			printf("(%d,%d) ",queenxpos[j],j);
		}
		printf("\n");
	} else if(total_solutions==max_solutions_printed) {
		printf("large number of solutions, stopped printing...\n");
	}
	total_solutions++;
}

void nqueens_search( int queenxpos[SIZE], int ypos )
{
	/* Consider every xpos in the row for this ypos: */
	for( int xpos=0; xpos<SIZE; xpos++ ) {

		/* Consider a queen placed at xpos, ypos. */
		/* Skip unsafe locations. */
	  
		if(any_in_same_column(queenxpos,xpos,ypos)) continue;
		if(any_in_same_diagonal(queenxpos,xpos,ypos)) continue;

		/* Then place a queen here */
		queenxpos[ypos] = xpos;

		/* Did we make it to the last row? */
		if( ypos==SIZE-1 ) {
			/* Yes - display one solution. */
			nqueens_print(queenxpos);
		} else {
			/* Not yet - work the next row. */
			nqueens_search(queenxpos,ypos+1);
		}
	}
}

int main( int argc, char *argv[] )
{
	/* Mark the start of the experiment. */
	struct timeval start;  
	gettimeofday(&start,0);

	int queenxpos[SIZE];
	nqueens_search(queenxpos,0);

	/* Mark the stop of the experiment. */
	struct timeval stop;  
	gettimeofday(&stop,0);

	/* Elapsed is the difference between the two */
	struct timeval elapsed;
	timersub(&stop,&start,&elapsed);

	printf("elapsed: %u.%0.6u solutions: %d\n",elapsed.tv_sec,elapsed.tv_usec,total_solutions);

	return 0;
}
