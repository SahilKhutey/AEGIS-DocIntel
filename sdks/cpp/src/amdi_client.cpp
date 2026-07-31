#include "amdi_sdk/amdi_client.hpp"

namespace amdi {

AmdiClient::AmdiClient(std::string target, std::string api_key)
    : target_(std::move(target)), api_key_(std::move(api_key)) {}

AmdiClient::~AmdiClient() = default;

} // namespace amdi
