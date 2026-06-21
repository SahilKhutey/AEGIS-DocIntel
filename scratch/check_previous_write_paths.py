import json

transcript_path = r"C:\Users\User\.gemini\antigravity\brain\b61e9a5c-8834-495a-897b-a098c755cb94\.system_generated\logs\transcript_full.jsonl"

print("Searching transcript for write_to_file calls...")
with open(transcript_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "write_to_file" in line or "replace_file_content" in line:
            try:
                data = json.loads(line)
                calls = data.get("tool_calls", [])
                for call in calls:
                    name = call.get("name")
                    args = call.get("args", {})
                    target = args.get("TargetFile")
                    if target and (".md" in target or "Architecture" in target or "Systems" in target):
                        print(f"Line {i}: tool={name} target={target}")
            except Exception:
                pass
