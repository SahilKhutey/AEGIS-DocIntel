# AEGIS-DocIntel C++ SDK

C++ client for AEGIS-DocIntel gRPC service.

```cpp
#include "amdi_sdk/amdi_client.hpp"

int main() {
    amdi::AmdiClient client("localhost:50051", "api-key");
    auto health = client.Health();
    return 0;
}
```
