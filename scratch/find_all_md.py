import os

workspace = r"c:\Users\User\Documents\AEGIS-DocIntel"

print("Searching workspace for all .md files...")
for root, dirs, files in os.walk(workspace):
    for f in files:
        if f.lower().endswith(".md"):
            print(os.path.join(root, f))
