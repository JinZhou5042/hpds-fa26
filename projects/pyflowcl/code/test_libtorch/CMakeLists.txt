cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project(conv_FD)

find_package(Torch REQUIRED)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${TORCH_CXX_FLAGS}")

add_executable(conv_FD conv_FD.cpp)
target_link_libraries(conv_FD "${TORCH_LIBRARIES}")
set_property(TARGET conv_FD PROPERTY CXX_STANDARD 14)
