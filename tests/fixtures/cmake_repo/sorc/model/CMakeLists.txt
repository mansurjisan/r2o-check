cmake_minimum_required(VERSION 3.15)
project(model VERSION 1.0.0 LANGUAGES Fortran)

add_executable(model main.f90)

install(TARGETS model DESTINATION bin)
