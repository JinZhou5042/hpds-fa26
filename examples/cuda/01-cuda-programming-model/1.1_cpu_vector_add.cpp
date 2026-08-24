/*
 * From this topic directory:
 *   make 1.1_cpu_vector_add
 *   make condor_run build/1.1_cpu_vector_add
 *   make condor_submit build/1.1_cpu_vector_add
 *
 * Section 1.1: Understand ordinary CPU vector addition
 *
 * Start with the CPU loop that later CUDA versions will replace:
 *
 *     C[i] = A[i] + B[i]
 *
 * One CPU thread handles every element. The CUDA version assigns one element
 * to each GPU thread.
 *
 * This is data parallelism: every element uses the same independent operation.
 * The pointer comments below spell out the C++ syntax used again in the CUDA
 * versions.
 */

#include <cstddef>
#include <iostream>
#include <vector>

void vector_add_cpu(const float* a, const float* b, float* c, std::size_t n) {
    /*
     * a, b, and c are pointers. You can think of them as the starting
     * addresses of three arrays. The expression a[i] is equivalent to
     * *(a + i): move i float elements beyond the starting address and access
     * that element.
     *
     * const on a and b promises that this function only reads those arrays.
     * Statements such as a[i] = 1 are therefore rejected by the compiler.
     * c is not const because this function must write the output into it.
     *
     * std::size_t is the unsigned integer type used by C++ for object sizes
     * and array indices. It can represent the largest object supported by the
     * current platform, which makes it a better choice than an arbitrary int.
     */
    for (std::size_t i = 0; i < n; ++i) {
        // The CPU thread executes n iterations; iteration i computes C[i].
        c[i] = a[i] + b[i];
    }
}

int main() {
    /*
     * std::vector<float> owns a contiguous region of float elements and
     * releases that memory automatically when the vector leaves scope. Small,
     * fixed inputs make the expected result easy to verify by hand.
     *
     * a and b are const, so the inputs cannot be changed after construction.
     */
    const std::vector<float> a{1.0f, 2.0f, 3.0f, 4.0f};
    const std::vector<float> b{10.0f, 20.0f, 30.0f, 40.0f};

    // Supplying only a length value-initializes these float elements to 0.
    std::vector<float> c(a.size());

    /*
     * data() returns the address of the first element in the contiguous
     * storage, which matches the function's pointer parameters. size() returns
     * an element count, not a byte count; it returns 4 in this example.
     *
     * The function can have return type void because c.data() gives it access
     * to memory owned by the caller. Writing through c directly changes the
     * caller's output vector.
     */
    vector_add_cpu(a.data(), b.data(), c.data(), a.size());

    // The expected values are 11, 22, 33, and 44.
    for (std::size_t i = 0; i < c.size(); ++i) {
        std::cout << "c[" << i << "] = " << c[i] << '\n';
    }
}

/*
 * Performance perspective
 * -----------------------
 * For N elements, the loop performs:
 *
 * - N floating-point additions;
 * - N reads from A;
 * - N reads from B;
 * - N writes to C.
 *
 * A float occupies 4 bytes, so the idealized algorithmic traffic is about 12N
 * bytes while the arithmetic work is only N additions. There is very little
 * computation per byte moved. Large vector additions are therefore usually
 * limited by memory bandwidth rather than floating-point compute throughput.
 *
 * With -O2 or -O3, the compiler may automatically vectorize this loop and use
 * CPU SIMD instructions. The later "CPU baseline" is therefore an optimized
 * host implementation, not necessarily one scalar instruction at a time.
 */
