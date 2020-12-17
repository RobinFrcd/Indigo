find_program(CCACHE_PROGRAM ccache)
if (CCACHE_PROGRAM)
    message(STATUS "Using ccache to increase compile speed: ${CCACHE_PROGRAM}")
    set(CMAKE_CXX_COMPILER_LAUNCHER "${CCACHE_PROGRAM}")
endif ()

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif ()

if (EMSCRIPTEN)
    string(APPEND CMAKE_CXX_FLAGS " -c")
    string(APPEND CMAKE_C_FLAGS   " -c")

    set(CMAKE_CXX_FLAGS_RELEASE "-Oz -DNDEBUG -flto")
    set(CMAKE_C_FLAGS_RELEASE   "-Oz -DNDEBUG -flto")

    set(CMAKE_CXX_FLAGS_DEBUG "-g -Oz -flto")
    set(CMAKE_C_FLAGS_DEBUG   "-g -Oz -flto")

    set(CMAKE_C_OUTPUT_EXTENSION   ".bc")
    set(CMAKE_CXX_OUTPUT_EXTENSION ".bc")

    set(CMAKE_AR "emar")
    set(CMAKE_C_CREATE_STATIC_LIBRARY   "<CMAKE_AR> qc <TARGET> <LINK_FLAGS> <OBJECTS>")
    set(CMAKE_CXX_CREATE_STATIC_LIBRARY "<CMAKE_AR> qc <TARGET> <LINK_FLAGS> <OBJECTS>")

    #string(APPEND CMAKE_CXX_FLAGS " -s ALLOW_MEMORY_GROWTH=1 -s DISABLE_EXCEPTION_CATCHING=0")  #
    #string(APPEND CMAKE_C_FLAGS   " -s ALLOW_MEMORY_GROWTH=1 -s DISABLE_EXCEPTION_CATCHING=0")  #
    #string(APPEND CMAKE_SHARED_LINKER_FLAGS " -s SIDE_MODULE=1 -s EXPORT_ALL=1 -s STANDALONE_WASM=1")
    # string(APPEND CMAKE_STATIC_LINKER_FLAGS " -s SIDE_MODULE=1 -s EXPORT_ALL=1 -s STANDALONE_WASM=1")
    #string(APPEND CMAKE_CXX_FLAGS_RELEASE " -flto")
    #string(APPEND CMAKE_C_FLAGS_RELEASE   " -flto")
    # set(CMAKE_SHARED_LIBRARY_SUFFIX  ".wasm")
    # set(CMAKE_STATIC_LIBRARY_SUFFIX ".bc")
    # set(CMAKE_AR "emcc")
    # set(CMAKE_C_CREATE_STATIC_LIBRARY "<CMAKE_AR> -o <TARGET> <LINK_FLAGS> <OBJECTS>")
    # set(CMAKE_CXX_CREATE_STATIC_LIBRARY "<CMAKE_AR> -o <TARGET> <LINK_FLAGS> <OBJECTS>")
    #string(APPEND CMAKE_CXX_FLAGS_DEBUG " -s WASM=0")  # -s EMULATE_FUNCTION_POINTER_CASTS=1 -s DEMANGLE_SUPPORT=1  -O1 --source-map-base localhost:8080  -fsanitize=undefined -s ASSERTIONS=2 -s SAFE_HEAP=1 -s STACK_OVERFLOW_CHECK=2  --profiling
    #string(APPEND CMAKE_C_FLAGS_DEBUG   " -s WASM=0")  # -s EMULATE_FUNCTION_POINTER_CASTS=1 -s DEMANGLE_SUPPORT=1 -O1  --source-map-base localhost:8080  #  -fsanitize=undefined  -s ASSERTIONS=2 -s SAFE_HEAP=1 -s STACK_OVERFLOW_CHECK=2  --profiling
    # set(CMAKE_EXECUTABLE_SUFFIX ".wasm")
endif()
if (UNIX)
    string(APPEND CMAKE_C_FLAGS " -fvisibility=hidden")
    string(APPEND CMAKE_CXX_FLAGS " -fvisibility=hidden -fvisibility-inlines-hidden")
    if (BUILD_SELF_SUFFICIENT AND NOT EMSCRIPTEN)
        if (CMAKE_CXX_COMPILER_ID STREQUAL GNU)
            string(APPEND CMAKE_CXX_FLAGS " -static-libstdc++")
        elseif  (CMAKE_CXX_COMPILER_ID STREQUAL Clang)
            string(APPEND CMAKE_CXX_FLAGS " -Wall -Wextra -stdlib=libc++")
        endif()
    else ()
        list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
    endif ()
endif ()

set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

if (ENABLE_TESTS)
    enable_testing()
endif ()

if (BUILD_SELF_SUFFICIENT AND BUILD_SELF_SUFFICIENT_CONAN)
    include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/conan.cmake)
endif ()

find_package(Threads REQUIRED)

set(DIST_DIRECTORY ${CMAKE_SOURCE_DIR}/dist)
set(INDIGO_NATIVE_LIBS_DIRECTORY ${DIST_DIRECTORY}/lib)

string(TOLOWER ${CMAKE_SYSTEM_NAME} CMAKE_SYSTEM_NAME_LOWER)
