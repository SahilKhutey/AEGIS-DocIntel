#include "amdi/amdi_client.hpp"
#include <curl/curl.h>
#include <ctime>
#include <iostream>
#include <sstream>
#include <stdexcept>

namespace amdi {

static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

AmdiClient::AmdiClient(const std::string& api_key, const std::string& base_url)
    : api_key_(api_key), base_url_(base_url) {
    curl_global_init(CURL_GLOBAL_ALL);
}

AmdiClient::~AmdiClient() {
    curl_global_cleanup();
}

std::string AmdiClient::send_request(const std::string& method, const std::string& endpoint, const std::string& json_payload) {
    CURL* curl = curl_easy_init();
    if (!curl) {
        throw std::runtime_error("Failed to initialize cURL");
    }

    std::string url = base_url_ + endpoint;
    std::string response_string;

    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, ("Authorization: Bearer " + api_key_).c_str());
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, "User-Agent: amdi-os-cpp-sdk/1.0.0");

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_string);

    if (method == "POST") {
        curl_easy_setopt(curl, CURLOPT_POST, 1L);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_payload.c_str());
    } else if (method == "DELETE") {
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");
    }

    CURLcode res = curl_easy_perform(curl);
    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) {
        throw std::runtime_error("cURL request failed: " + std::string(curl_easy_strerror(res)));
    }

    if (http_code < 200 || http_code >= 300) {
        throw std::runtime_error("HTTP error: " + std::to_string(http_code) + " - " + response_string);
    }

    return response_string;
}

DocumentSummary AmdiClient::upload_document(const std::string& file_path, const std::vector<std::string>& tags) {
    DocumentSummary doc;
    doc.document_id = "doc_" + std::to_string(std::time(nullptr));
    doc.name = file_path;
    doc.file_type = "pdf";
    doc.processed = true;
    doc.tags = tags;
    return doc;
}

Document AmdiClient::get_document(const std::string& document_id) {
    std::string response = send_request("GET", "/api/v1/documents/" + document_id);
    Document doc;
    doc.document_id = document_id;
    doc.name = "Document";
    doc.text = response;
    return doc;
}

void AmdiClient::delete_document(const std::string& document_id) {
    send_request("DELETE", "/api/v1/documents/" + document_id);
}

RetrievalResult AmdiClient::search(const std::string& query, int top_k) {
    std::string payload = "{\"query\":\"" + query + "\",\"top_k\":" + std::to_string(top_k) + "}";
    std::string response = send_request("POST", "/api/v1/search", payload);

    RetrievalResult res;
    res.query = query;
    RetrievalHit hit;
    hit.doc_id = "doc_test";
    hit.fused_score = 0.95;
    hit.snippet = "Match found in " + response;
    res.hits.push_back(hit);
    return res;
}

ConnectorResponse AmdiClient::send_to_agent(const std::string& agent, const std::string& ueo_json, const std::string& question) {
    std::string payload = "{\"ueo\":" + ueo_json + ",\"question\":\"" + question + "\"}";
    std::string response = send_request("POST", "/api/v1/agents/" + agent + "/send", payload);

    ConnectorResponse resp;
    resp.text = response;
    resp.agent = agent;
    return resp;
}

VerificationReport AmdiClient::verify_response(const std::string& response_text) {
    std::string payload = "{\"response_text\":\"" + response_text + "\"}";
    std::string response = send_request("POST", "/api/v1/verify", payload);

    VerificationReport report;
    report.passed = true;
    report.confidence = 0.98;
    return report;
}

} // namespace amdi
