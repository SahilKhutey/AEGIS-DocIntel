#pragma once

#include <map>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace amdi {

struct DocumentSummary {
    std::string document_id;
    std::string name;
    std::string file_type;
    long long size_bytes = 0;
    int page_count = 0;
    std::string uploaded_at;
    bool processed = false;
    std::vector<std::string> tags;
};

struct Document {
    std::string document_id;
    std::string name;
    std::string file_type;
    long long size_bytes = 0;
    int page_count = 0;
    std::string text;
};

struct RetrievalHit {
    std::string doc_id;
    double fused_score = 0.0;
    std::vector<std::string> methods_found;
    std::string snippet;
};

struct RetrievalResult {
    std::string query;
    std::vector<RetrievalHit> hits;
    double latency_ms = 0.0;
    int total_candidates = 0;
};

struct ConnectorResponse {
    std::string text;
    std::string agent;
    std::string model;
    bool success = true;
    std::string error;
};

struct VerificationReport {
    bool passed = false;
    double confidence = 0.0;
    std::string grade;
    std::vector<std::string> issues;
};

class AmdiClient {
public:
    AmdiClient(const std::string& api_key, const std::string& base_url = "https://api.amdi-os.com");
    ~AmdiClient();

    // Documents
    DocumentSummary upload_document(const std::string& file_path, const std::vector<std::string>& tags = {});
    Document get_document(const std::string& document_id);
    void delete_document(const std::string& document_id);

    // Retrieval
    RetrievalResult search(const std::string& query, int top_k = 10);

    // Agents
    ConnectorResponse send_to_agent(const std::string& agent, const std::string& ueo_json, const std::string& question = "");

    // Verification
    VerificationReport verify_response(const std::string& response_text);

private:
    std::string api_key_;
    std::string base_url_;
    
    std::string send_request(const std::string& method, const std::string& endpoint, const std::string& json_payload = "");
};

} // namespace amdi
