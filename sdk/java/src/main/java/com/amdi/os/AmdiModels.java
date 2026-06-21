package com.amdi.os;

import java.util.List;
import java.util.Map;

public class AmdiModels {

    public static class DocumentSummary {
        public String document_id;
        public String name;
        public String file_type;
        public long size_bytes;
        public int page_count;
        public String uploaded_at;
        public boolean processed;
        public List<String> tags;
        public Map<String, Object> metadata;
    }

    public static class Document {
        public String document_id;
        public String name;
        public String file_type;
        public long size_bytes;
        public int page_count;
        public String text;
        public Map<String, Object> metadata;
        public Map<String, Object> engine_reports;
    }

    public static class RetrievalHit {
        public String doc_id;
        public double fused_score;
        public List<String> methods_found;
        public Map<String, Double> per_method_score;
        public String snippet;
    }

    public static class RetrievalResult {
        public String query;
        public List<RetrievalHit> hits;
        public Map<String, Integer> per_method_counts;
        public double latency_ms;
        public int total_candidates;
    }

    public static class Citation {
        public String doc_id;
        public Integer page;
        public String section;
        public String excerpt;
    }

    public static class UniversalExportObject {
        public String system;
        public String context;
        public String summary;
        public List<Citation> citations;
        public Map<String, Object> metadata;
        public double confidence;
        public int total_tokens;
        public Map<String, Object> agent_specific;
        public String version;
    }

    public static class ConnectorResponse {
        public String text;
        public String agent;
        public String model;
        public Map<String, Integer> usage;
        public String finish_reason;
        public double latency_ms;
        public Map<String, Object> metadata;
        public boolean success;
        public String error;
    }

    public static class EngineOutput {
        public String engine_name;
        public Map<String, Object> data;
        public double confidence;
        public double latency_ms;
    }

    public static class VerificationReport {
        public boolean passed;
        public double confidence;
        public String grade;
        public double citation_accuracy;
        public double fact_accuracy;
        public double hallucination_rate;
        public List<String> issues;
        public String recommendation;
    }
}
