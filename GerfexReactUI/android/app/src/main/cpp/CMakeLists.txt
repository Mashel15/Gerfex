cmake_minimum_required(VERSION 3.22.1)

project(gerfex_llama_jni)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PREBUILT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/prebuilt/${ANDROID_ABI})

add_library(llama SHARED IMPORTED)
set_target_properties(llama PROPERTIES IMPORTED_LOCATION ${PREBUILT_DIR}/libllama.so)

add_library(ggml SHARED IMPORTED)
set_target_properties(ggml PROPERTIES IMPORTED_LOCATION ${PREBUILT_DIR}/libggml.so)

add_library(ggml-base SHARED IMPORTED)
set_target_properties(ggml-base PROPERTIES IMPORTED_LOCATION ${PREBUILT_DIR}/libggml-base.so)

add_library(omp SHARED IMPORTED)
set_target_properties(omp PROPERTIES IMPORTED_LOCATION ${PREBUILT_DIR}/libomp.so)

add_library(
    gerfex_llama_jni
    SHARED
    gerfex_llama_jni.cpp
)

target_include_directories(
    gerfex_llama_jni
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/llama_include/include
    ${CMAKE_CURRENT_SOURCE_DIR}/llama_include/ggml/include
)

find_library(log-lib log)

target_link_libraries(
    gerfex_llama_jni
    llama
    ggml
    ggml-base
    omp
    ${log-lib}
    dl
)
