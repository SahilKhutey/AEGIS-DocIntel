import os
import json

brain_dir = r"C:\Users\User\.gemini\antigravity\brain"

print("Searching all conversation directories for Mathematics.md content...")
matches = []

for entry in os.listdir(brain_dir):
    dir_path = os.path.join(brain_dir, entry)
    if os.path.isdir(dir_path):
        logs_dir = os.path.join(dir_path, ".system_generated", "logs")
        if os.path.exists(logs_dir):
            for log_file in ["transcript_full.jsonl", "transcript.jsonl"]:
                log_path = os.path.join(logs_dir, log_file)
                if os.path.exists(log_path):
                    try:
                        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line_no, line in enumerate(f):
                                if "Mathematics.md" in line and "6\\ufe0f\\u20e3" in line:
                                    matches.append((log_path, line_no, len(line)))
                                    # Print a small snippet
                                    idx = line.find("Mathematics.md")
                                    print(f"Match found in {log_path} at line {line_no}")
                    except Exception as e:
                        pass

print(f"\nDone. Found {len(matches)} matches.")
