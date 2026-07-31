#include <iostream>
#include "amdi_sdk/amdi_client.hpp"

int main() {
    amdi::AmdiClient client("localhost:50051", "demo-api-key");
    std::cout << "AmdiClient initialized.\n";
    return 0;
}
