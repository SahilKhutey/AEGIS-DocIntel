with open("tests/test_graph.py", "r", encoding="utf-8") as f:
    text = f.read()

# Normalize line endings
text = text.replace("\r\n", "\n").replace("\r", "\n")
lines = text.splitlines()

formatted = []
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == "":
        # It's a blank line. Let's decide whether to keep it.
        if i == 0 or i == len(lines) - 1:
            continue
        prev_line = lines[i-1].strip()
        next_line = lines[i+1].strip()
        
        # Don't keep blank lines if they are inside a list/tuple definition or inside an import block
        if prev_line.endswith("(") or prev_line.endswith("[") or prev_line.endswith(",") or prev_line.endswith("\\"):
            continue
        if next_line.startswith(")") or next_line.startswith("]") or next_line.startswith("}"):
            continue
        if prev_line.startswith("from ") or prev_line.startswith("import "):
            if next_line.startswith("from ") or next_line.startswith("import "):
                continue
                
        # Keep a single blank line before function definitions, class definitions, or section comments
        if next_line.startswith("def ") or next_line.startswith("class ") or next_line.startswith("# =="):
            if not formatted or formatted[-1] != "":
                formatted.append("")
            continue
            
        # Collapse multiple consecutive blank lines
        if formatted and formatted[-1] == "":
            continue
            
        # Default: keep the blank line if it's separating logical blocks in a function
        # but let's be conservative: don't keep too many blank lines inside functions
        if prev_line.startswith("def ") or prev_line.startswith("class ") or prev_line == "":
            continue
            
        formatted.append("")
    else:
        formatted.append(line.rstrip())

# Let's write the result back
with open("tests/test_graph.py", "w", encoding="utf-8") as f:
    f.write("\n".join(formatted) + "\n")

print("Spacings in test_graph.py cleaned successfully!")
