#include <stdio.h>
#include <omp.h>

int main()
{
        printf("omp max_threads=%d cores=%d\n",omp_get_max_threads(),omp_get_num_procs());

	printf("omp sections: every section done by one thread\n");
	#pragma omp parallel
	{
		#pragma omp sections
		{
			#pragma omp section
			{
				for(int i=0;i<5;i++) {
					printf("thread=%d i=%d\n",omp_get_thread_num(),i);
				}
			}

			#pragma omp section
			{
				for(int k=8;k>=1;k=k/2) {
					printf("thread=%d k=%d\n",omp_get_thread_num(),k);
				}
			}
		}
		printf("all done! (thread %d)\n",omp_get_thread_num());

	}

	return 0;	
}

