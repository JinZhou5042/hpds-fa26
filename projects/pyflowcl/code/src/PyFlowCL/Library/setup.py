from setuptools import setup, Extension
from torch.utils import cpp_extension

def get_extensions():
    # Only import inside the function to avoid global import error
    from torch.utils import cpp_extension
    return [
        cpp_extension.CppExtension(name='solver_cpp', sources=['Solver.cpp'])
    ]

setup(
    name='solver_cpp',
    # ext_modules=[cpp_extension.CppExtension(name='solver_cpp', 
    #                                         sources=['Solver.cpp'])
    # ],
    # cmdclass={
    #     'build_ext': cpp_extension.BuildExtension
    # }
    
    ext_modules=get_extensions(),
    # Note: BuildExtension still needs to be referenced
    cmdclass={'build_ext': __import__('torch.utils.cpp_extension').utils.cpp_extension.BuildExtension}
)
