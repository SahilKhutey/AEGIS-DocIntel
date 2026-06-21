import os
import re

path = r"C:\Users\User\.gemini\antigravity\brain\b61e9a5c-8834-495a-897b-a098c755cb94\scratch\documentation_request_untruncated.txt"
output_dir = r"c:\Users\User\Documents\AEGIS-DocIntel\docs"
os.makedirs(output_dir, exist_ok=True)

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Define headers in the file
headers = [
    ("1\ufe0f\u20e3 README.md", "README.md"),
    ("## 2\ufe0f\u20e3 `Architecture.md`", "Architecture.md"),
    ("3\ufe0f\u20e3 Design.md", "Design.md"),
    ("## 4\ufe0f\u20e3 `Systems.md`", "Systems.md"),
    ("## 5\ufe0f\u20e3 `Workflow.md`", "Workflow.md")
]

found = []
for h_pattern, filename in headers:
    pos = content.find(h_pattern)
    if pos != -1:
        found.append((pos, h_pattern, filename))
    else:
        print(f"Pattern '{h_pattern}' not found!")

found.sort()

for idx, (pos, h_pattern, filename) in enumerate(found):
    start = pos + len(h_pattern)
    end = len(content)
    for next_pos, _, _ in found[idx+1:]:
        if next_pos > start:
            end = next_pos
            break
    
    subcontent = content[start:end].strip()
    
    # Clean markdown block if present
    if subcontent.startswith("```markdown"):
        subcontent = subcontent[11:]
    elif subcontent.startswith("```"):
        subcontent = subcontent[3:]
        
    if subcontent.endswith("```"):
        subcontent = subcontent[:-3]
        
    subcontent = subcontent.strip()
    
    # README goes to root, others go to docs/
    if filename == "README.md":
        dest_path = r"c:\Users\User\Documents\AEGIS-DocIntel\README.md"
    else:
        dest_path = os.path.join(output_dir, filename)
        
    with open(dest_path, "w", encoding="utf-8") as out:
        out.write(subcontent)
    print(f"Extracted {filename} to {dest_path} ({len(subcontent)} bytes)")
