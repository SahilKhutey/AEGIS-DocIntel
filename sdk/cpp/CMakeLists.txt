cmake_minimum_required(VERSION 3.12)
project(amdi-os-cpp-sdk VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find cURL
find_package(CURL REQUIRED)

# Include directories
include_directories(include)

# Define library
add_library(amdi_client
    src/amdi_client.cpp
)

# Target include directories
target_include_directories(amdi_client PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Target link libraries
target_link_libraries(amdi_client PRIVATE
    CURL::libcurl
)
