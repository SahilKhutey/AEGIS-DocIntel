import re

path = r"C:\Users\User\.gemini\antigravity\brain\b61e9a5c-8834-495a-897b-a098c755cb94\scratch\documentation_request_untruncated.txt"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Find headers like 1️⃣, 2️⃣, 3️⃣, etc.
matches = re.finditer(r'([0-9]️⃣\s+\w+\.md)', content)
for m in matches:
    raw_str = m.group(0)
    ascii_str = raw_str.encode('ascii', 'backslashreplace').decode('ascii')
    print(f"Found at position {m.start()}: {ascii_str}")
