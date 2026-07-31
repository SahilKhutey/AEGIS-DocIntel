cmake_minimum_required(VERSION 3.20)
project(amdi-sdk CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Protobuf REQUIRED)
find_package(gRPC REQUIRED)

set(SOURCES src/amdi_client.cpp)
set(HEADERS include/amdi_sdk/amdi_client.hpp)

add_library(amdi_sdk STATIC ${SOURCES} ${HEADERS})
target_include_directories(amdi_sdk PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${Protobuf_INCLUDE_DIRS}
    ${gRPC_INCLUDE_DIRS})
target_link_libraries(amdi_sdk PUBLIC
    protobuf::libprotobuf
    gRPC::grpc++
    gRPC::grpc)

add_executable(upload_example examples/upload.cpp)
target_link_libraries(upload_example PRIVATE amdi_sdk)
