# AMDI-OS C++ SDK

Official C++ client for the **Adaptive Mathematical Document Intelligence Operating System**.

## Prerequisites

- CMake >= 3.12
- libcurl
- A C++17 compatible compiler

## Quick Start

### CMake Integration

Add the directory to your project and link the target:

```cmake
add_subdirectory(sdk/cpp)
target_link_libraries(your_target PRIVATE amdi_client)
```

### Usage Example

```cpp
#include "amdi/amdi_client.hpp"
#include <iostream>

int main() {
    try {
        amdi::AmdiClient client("your-api-key", "https://api.amdi-os.com");

        // Upload a document
        amdi::DocumentSummary doc = client.upload_document("contract.pdf");
        std::cout << "Uploaded: " << doc.document_id << std::endl;

        // Perform hybrid search
        amdi::RetrievalResult search_res = client.search("What is SVD?", 5);
        for (const auto& hit : search_res.hits) {
            std::cout << "Hit doc: " << hit.doc_id << ", score: " << hit.fused_score << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}
```
