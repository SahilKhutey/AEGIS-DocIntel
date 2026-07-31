#pragma once
#include <memory>
#include <string>
#include <vector>

namespace amdi {

class AmdiClient {
public:
    explicit AmdiClient(std::string target, std::string api_key = "");
    ~AmdiClient();

private:
    std::string target_;
    std::string api_key_;
};

} // namespace amdi
