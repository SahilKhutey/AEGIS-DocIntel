package com.amdi.os;

import com.amdi.os.exceptions.AmdiException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Path;
import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class AmdiClient {
    private final String apiKey;
    private final String baseUrl;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    public final DocumentsAPI documents;
    public final RetrievalAPI retrieval;
    public final ContextAPI context;
    public final AgentsAPI agents;
    public final VerificationAPI verification;
    public final EnginesAPI engines;
    public final MemoryAPI memory;

    public AmdiClient(String apiKey) {
        this(apiKey, "https://api.amdi-os.com");
    }

    public AmdiClient(String apiKey, String baseUrl) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
        this.objectMapper = new ObjectMapper();

        this.documents = new DocumentsAPI();
        this.retrieval = new RetrievalAPI();
        this.context = new ContextAPI();
        this.agents = new AgentsAPI();
        this.verification = new VerificationAPI();
        this.engines = new EnginesAPI();
        this.memory = new MemoryAPI();
    }

    private <T> T sendRequest(String method, String endpoint, Object body, Class<T> responseType) {
        try {
            String jsonBody = body != null ? objectMapper.writeValueAsString(body) : "";
            HttpRequest.Builder builder = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + endpoint))
                    .header("Authorization", "Bearer " + apiKey)
                    .header("Content-Type", "application/json")
                    .header("User-Agent", "amdi-os-java-sdk/1.0.0");

            if (method.equals("GET")) {
                builder.GET();
            } else if (method.equals("POST")) {
                builder.POST(HttpRequest.BodyPublishers.ofString(jsonBody));
            } else if (method.equals("DELETE")) {
                builder.DELETE();
            } else if (method.equals("PUT")) {
                builder.PUT(HttpRequest.BodyPublishers.ofString(jsonBody));
            }

            HttpResponse<String> response = httpClient.send(builder.build(), HttpResponse.BodyHandlers.ofString());
            int status = response.statusCode();
            if (status >= 200 && status < 300) {
                if (responseType == Void.class) {
                    return null;
                }
                return objectMapper.readValue(response.body(), responseType);
            }
            throw new AmdiException("HTTP error: " + status, status, response.body());
        } catch (IOException | InterruptedException e) {
            throw new AmdiException("Request failed: " + e.getMessage());
        }
    }

    public class DocumentsAPI {
        public AmdiModels.DocumentSummary upload(Path filePath) {
            try {
                String boundary = "---AMDISDKBoundary" + System.currentTimeMillis();
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(baseUrl + "/api/v1/documents"))
                        .header("Authorization", "Bearer " + apiKey)
                        .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                        .POST(HttpRequest.BodyPublishers.ofFile(filePath))
                        .build();
                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
                if (response.statusCode() >= 200 && response.statusCode() < 300) {
                    return objectMapper.readValue(response.body(), AmdiModels.DocumentSummary.class);
                }
                throw new AmdiException("Upload failed: " + response.statusCode(), response.statusCode(), response.body());
            } catch (IOException | InterruptedException e) {
                throw new AmdiException("Upload failed: " + e.getMessage());
            }
        }

        public AmdiModels.Document get(String documentId) {
            return sendRequest("GET", "/api/v1/documents/" + documentId, null, AmdiModels.Document.class);
        }

        public void delete(String documentId) {
            sendRequest("DELETE", "/api/v1/documents/" + documentId, null, Void.class);
        }
    }

    public class RetrievalAPI {
        public AmdiModels.RetrievalResult search(String query, int topK) {
            Map<String, Object> body = new HashMap<>();
            body.put("query", query);
            body.put("top_k", topK);
            return sendRequest("POST", "/api/v1/search", body, AmdiModels.RetrievalResult.class);
        }
    }

    public class ContextAPI {
        public AmdiModels.UniversalExportObject build(List<Map<String, Object>> candidates, int totalBudget) {
            Map<String, Object> body = new HashMap<>();
            body.put("candidates", candidates);
            body.put("total_budget", totalBudget);
            return sendRequest("POST", "/api/v1/context", body, AmdiModels.UniversalExportObject.class);
        }
    }

    public class AgentsAPI {
        public AmdiModels.ConnectorResponse send(String agent, AmdiModels.UniversalExportObject ueo, String question) {
            Map<String, Object> body = new HashMap<>();
            body.put("ueo", ueo);
            body.put("question", question);
            return sendRequest("POST", "/api/v1/agents/" + agent + "/send", body, AmdiModels.ConnectorResponse.class);
        }
    }

    public class VerificationAPI {
        public AmdiModels.VerificationReport verify(String responseText) {
            Map<String, Object> body = new HashMap<>();
            body.put("response_text", responseText);
            return sendRequest("POST", "/api/v1/verify", body, AmdiModels.VerificationReport.class);
        }
    }

    public class EnginesAPI {
        public AmdiModels.EngineOutput run(String engine, String documentId) {
            Map<String, Object> body = new HashMap<>();
            body.put("document_id", documentId);
            return sendRequest("POST", "/api/v1/engines/" + engine + "/run", body, AmdiModels.EngineOutput.class);
        }
    }

    public class MemoryAPI {
        public Map<String, Object> getStats() {
            return sendRequest("GET", "/api/v1/memory/stats", null, Map.class);
        }
    }
}
