import re

with open("tests/test_graph.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace literal '\\n' or '\n' text with actual newlines
# Wait, let's see how they are represented in the file.
# In python string: content.replace("\\n", "\n")
cleaned = content.replace("\\n", "\n")

# Collapse multiple consecutive empty lines to a single empty line
lines = cleaned.splitlines()
output_lines = []
last_was_blank = False
for line in lines:
    if line.strip() == "":
        if not last_was_blank:
            output_lines.append("")
            last_was_blank = True
    else:
        output_lines.append(line)
        last_was_blank = False

with open("tests/test_graph.py", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines) + "\n")

print("test_graph.py formatted successfully!")
