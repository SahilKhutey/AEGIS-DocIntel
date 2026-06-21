import re

path = r"C:\Users\User\.gemini\antigravity\brain\b61e9a5c-8834-495a-897b-a098c755cb94\scratch\documentation_request_untruncated.txt"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

filenames = [
    "README.md", "Architecture.md", "Design.md", "Systems.md",
    "Workflow.md", "Mathematics.md", "Benchmarks.md", "Validation.md", "Deployment.md"
]

print("Searching lines for filenames...")
for i, line in enumerate(lines):
    for fn in filenames:
        if fn in line:
            # check if it looks like a header (e.g. starts with # or has a digit emoji)
            ascii_line = line.encode('ascii', 'backslashreplace').decode('ascii').strip()
            print(f"Line {i}: {ascii_line}")
