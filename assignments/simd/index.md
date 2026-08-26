# A1: SIMD Assignment

First review the [general instructions](../../general) for assignments.

- Explore the [Intel Intrinsics Guide](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html) and select three interesting operations (i.e. verbs) that we didn't discuss in class.  Describe each one in a paragraph that describes what it does, why it is interesting, and how you might use it in a program.

- Consult the [example experiment](../../simd/experiment) that we did in class as a model for organizing your work.

- Write a simple code kernel that reflects a common computation in an area that you know about (e.g. calculus, physics, chemistry, machine learning...).  Pick something a little more complicated than we did in class,
and use at least one of the new operations that you picked above.  Set up a "baseline" version like we did in class that uses SIZE and ITER, and prints out the elapsed time and checksum.  Adjust the parameters until it runs in 5-10 seconds.  (Make sure to compile this one `-O1` to prevent optimization.)

- Write an improved version that uses SIMD intrinsics to perform the kernel computation more efficiently.  Be caureful to ensure that you are computing exactly the same result, producing the same checksum for given values of SIZE and ITER.  (Make sure to compile this one `-O1 -mavx` to prevent optimization but allow your explicit SIMD intrinsics.)

- Evaluate the performance of the two versions as SIZE changes over a wide range, and plot the results.  Discuss the impact of using SIMD intrinsics.   (Do this on the ND CRC Front-End machines.)  If there isn't a meaningful difference between the two, go back to consider your code and compiler options to understand why.

- Reconsider your baseline code.  Without changing the original code, compile it with various optimization levels (`-O0` through `-O4`) and SIMD instruction sets (`-mmmx` `-msse` `-mavx` `-mavx2`) and `SIZE` values.  Plot the results and discuss -- how does the automatic vectorization compare to your manual efforts?

- Automatic vectorization only works if the underlying code is "easy" for the compiler to deal with:
data must be sequential, packed, aligned and operations must be consistent and done in bulk.
Ponder your baseline code carefully, and make a change to the organization that "hurts" the performance
in a substantial way, while still computing the same result.  Show that change and the impact on performance.

## Turning In

Commit all of your code, scripts, data, and plots to your course repository
in a directory called `simd`. Write a `README.md` that ties everything together and addresses the points above.
In all things, show insight, curiosity, and craftsmanship.
Turn in your work by submitting the URL of your repository to the corresponding
assignment page in Canvas.




