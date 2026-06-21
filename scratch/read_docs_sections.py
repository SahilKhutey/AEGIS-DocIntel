path = r"C:\Users\User\.gemini\antigravity\brain\b61e9a5c-8834-495a-897b-a098c755cb94\scratch\documentation_request_untruncated.txt"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Lines 540-560:")
for i in range(540, min(len(lines), 560)):
    print(f"Line {i}: {lines[i].encode('ascii', 'backslashreplace').decode('ascii').strip()}")

print("\nLines 1120-1135:")
for i in range(1120, min(len(lines), 1135)):
    print(f"Line {i}: {lines[i].encode('ascii', 'backslashreplace').decode('ascii').strip()}")

print("\nLines 1770-1785:")
for i in range(1770, min(len(lines), 1785)):
    print(f"Line {i}: {lines[i].encode('ascii', 'backslashreplace').decode('ascii').strip()}")
