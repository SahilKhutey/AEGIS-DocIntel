import os

patterns = [
    "dev-default-tenant",
    "dev-user",
    "dev@aegis.corp",
    "NEXT_PUBLIC_AEGIS_DEV_TOKEN",
    "aegis-dev-key",
    'startsWith("dev-")',
]

matched_records = []
for root, dirs, files in os.walk("."):
    if any(x in root for x in [".git", "node_modules", ".next", "__pycache__", ".pytest_cache", "brain", "audit"]):
        continue
    for file in files:
        filepath = os.path.join(root, file).replace("\\", "/")
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    for pat in patterns:
                        if pat in line:
                            matched_records.append(f"{filepath}:{line_num}: [{pat}] {line.strip()[:120]}")
        except Exception:
            pass

out_content = f"=== Baseline Auth Reference Scan ===\nTotal references: {len(matched_records)}\n\n" + "\n".join(matched_records) + "\n"
os.makedirs("audit/prot-04-02/baseline", exist_ok=True)
with open("audit/prot-04-02/baseline/auth-reference-scan.txt", "w", encoding="utf-8") as out:
    out.write(out_content)
print(f"Wrote {len(matched_records)} records to audit/prot-04-02/baseline/auth-reference-scan.txt")
