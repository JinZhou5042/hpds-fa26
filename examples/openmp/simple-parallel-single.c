#include <stdio.h>
#include <omp.h>

int main()
{
        printf("omp max_threads=%d cores=%d\n",omp_get_max_threads(),omp_get_num_procs());

	printf("omp single: bit of code should only be run by *one* thread\n");
	#pragma omp parallel
	{
		#pragma omp for
		for(int i=0;i<8;i++)
		{
                        printf("thread=%d i=%d\n",omp_get_thread_num(),i);
			
		}
		#pragma omp single
		{
			printf("all done! (thread %d)\n",omp_get_thread_num());
		}
	}

	return 0;	
}

