#include <stdio.h>
#include <omp.h>

int main()
{
	printf("omp max_threads=%d cores=%d\n",omp_get_max_threads(),omp_get_num_procs());
  
	printf("omp parallel: every thread does the same thing\n");
	#pragma omp parallel
	{
		for(int i=0;i<5;i++)
		{
			printf("thread=%d i=%d\n",omp_get_thread_num(),i);
		}
		printf("all done!\n");
	}

	return 0;	
}

