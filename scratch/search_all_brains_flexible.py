import os
import json

brain_dir = r"C:\Users\User\.gemini\antigravity\brain"

print("Searching all conversation directories flexibly for documentation content...")
matches = []

for entry in os.listdir(brain_dir):
    # skip current directory to keep it fast
    if entry == "b61e9a5c-8834-495a-897b-a098c755cb94":
        continue
    dir_path = os.path.join(brain_dir, entry)
    if os.path.isdir(dir_path):
        logs_dir = os.path.join(dir_path, ".system_generated", "logs")
        if os.path.exists(logs_dir):
            for log_file in ["transcript_full.jsonl"]:
                log_path = os.path.join(logs_dir, log_file)
                if os.path.exists(log_path):
                    try:
                        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line_no, line in enumerate(f):
                                if len(line) > 20000:  # Only look at large lines which could contain full docs
                                    if "Benchmarks.md" in line or "Validation.md" in line or "Deployment.md" in line:
                                        matches.append((log_path, line_no, len(line)))
                                        print(f"Match found in {log_path} at line {line_no}, len={len(line)}")
                    except Exception as e:
                        pass

print(f"\nDone. Found {len(matches)} matches.")
