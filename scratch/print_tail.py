path = r"C:\Users\User\.gemini\antigravity\brain\b61e9a5c-8834-495a-897b-a098c755cb94\scratch\documentation_request_untruncated.txt"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

print("Length of content:", len(content))
print("Last 1000 characters:")
tail = content[-1000:]
print(tail.encode('ascii', 'backslashreplace').decode('ascii'))
