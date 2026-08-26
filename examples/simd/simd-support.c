/* Display the various x86 SIMD options available on this machine. */

#include <iostream>
using namespace std;

int main() {

    cout << "float " << sizeof(float) << " bytes\n";
    cout << "double " << sizeof(double) << " bytes\n";
    cout << "short " << sizeof(short) << " bytes\n";
    cout << "int " << sizeof(int) << " bytes\n";
    cout << "long " << sizeof(long) << " bytes\n";

    cout << (__builtin_cpu_supports("sse") ? "sse" : "xxx")  << endl;
    cout << (__builtin_cpu_supports("sse2") ? "sse2" : "xxx") << endl;
    cout << (__builtin_cpu_supports("avx") ? "avx" : "xxx") << endl;
    cout << (__builtin_cpu_supports("avx2") ? "avx2" : "xxx") << endl;
    cout << (__builtin_cpu_supports("avx512f") ? "avx512f" : "xxx") << endl;

    return 0;
}
