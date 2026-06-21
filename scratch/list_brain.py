import os

brain_dir = r"C:\Users\User\.gemini\antigravity\brain"

print(f"Listing {brain_dir}...")
try:
    entries = os.listdir(brain_dir)
    print(f"Found {len(entries)} entries:")
    for entry in entries:
        path = os.path.join(brain_dir, entry)
        is_dir = os.path.isdir(path)
        print(f"  {'[DIR]' if is_dir else '[FILE]'} {entry}")
except Exception as e:
    print("Error:", e)
