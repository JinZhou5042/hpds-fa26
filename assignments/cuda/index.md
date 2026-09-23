# A3: CUDA Assignment

**Note 1**: Expect this assignment to take some time, so start well
in advance of the deadline.  Your jobs submitted to ND CRC and
Purdue Anvil may have to wait for resources to become available.

**Note 2**: There are a number of combinations here:
`benchmarks x improvements x sites x size`.
Be thoughtful in organizing your files and directories to keep track of everything.

First review the [general instructions](../../general) for assignments.

0 - Look up the available GPU devices and configurations available
at the Notre Dame CRC and Purdue Anvil. Dig down into the documentation
to determine the GPU model and look up the corresponding datasheet.
Report back on the number of GPUs per machinexs, number of cores per GPU,
technology generation (e.g. Pascal, Turing, Ampere), and quantity of GPU RAM.

1 - Explore the CUDA reference materials on the course web page.
Select two advanced CUDA capabilities that we didn't discuss in class.
Describe each one in a paragraph that describes what it does,
why it is interesting, and what sort of application might make use of it.

2 - Explore the [sequential benchmarks](https://github.com/dthain/hpds-fa26/tree/main/examples/benchmarks) presented in class.  Select *three* benchmarks to evaluate in CUDA.  One must be chosen from (fractal,matrix), one from (heat,nbody), and the third should be a completel different problem of interest to you.  For each benchmark, do the following:

a - Establish a sequential baseline.  Read the code to understand the fundamental operation. Adjust SIZE, ITER, DELTAT so that the benchmark runs in about 60s on a single core.
Make any adjustments needed to avoid excessive output.

b - Create an improved version of the benchmark that uses CUDA to execute in paralell
on the GPU.  Be creative and make use of appropriate CUDA features,
going beyond what we discussed in class.
(For this version, make sure that the benchmark allocates and copies data
in/out of the GPU on each iteration, so that your timing includes data movement.)

c - Create a third version of the benchmark that works the same as (b)
but keeps all data in the GPU between iterations.  Allocate and copy memory
and the beginning and end, but the GPU code should keep re-using data
in GPU memory at each iteration.   Take any other steps you think are
needed to improve performance.

3 - Evaluate the performance of your benchmarks on the GPU devices available
at the ND CRC for values of SIZE up to the maximum available GPU memory.
You may need to experiment to find the best thread block size.

4 - Evaluate the performance of your benchmarks on the GPU devices available
on Purdue Anvil for values of SIZE up to the maximum available GPU memory.
You may need to experiment to find the best thread block size.

5 - Plot your results, including the sequential baseline and the two CUDA versions
across the two facilities.
Discuss your results, in light of the data collected in step one.
Be sure to point out and explain any unexpected behaviors.
Take some time to think through the most clear and insightful way to plot your
data 

## Turning In

Commit all of your code, scripts, data, and plots to your course repository
in a directory called `cuda`.

Include a `README.md` written in the style of an engineering report that
explains your objectives, configuration, and experiments in a way that
would be understandable to someone outside the class.

Make sure to embed code links and plot images into the report so that
is is easy to read and follow.

In all things, show insight, curiosity, and craftsmanship.

Be sure to push everything to GitHub!

Turn in your work by submitting the URL of your repository to the corresponding
assignment page in Canvas.
