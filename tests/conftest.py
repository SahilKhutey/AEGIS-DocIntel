import os
import sys
from pathlib import Path

# Custom list subclass to block "amdi-os" from being added to sys.path
class ProtectedPathList(list):
    def insert(self, index, item):
        if "amdi-os" in str(item):
            return
        super().insert(index, item)

    def append(self, item):
        if "amdi-os" in str(item):
            return
        super().append(item)

    def extend(self, items):
        filtered = [i for i in items if "amdi-os" not in str(i)]
        super().extend(filtered)

    def __add__(self, other):
        filtered = [i for i in other if "amdi-os" not in str(i)]
        return ProtectedPathList(super().__add__(filtered))

    def __iadd__(self, other):
        filtered = [i for i in other if "amdi-os" not in str(i)]
        return super().__iadd__(filtered)

# Replace sys.path with our protected list
sys.path = ProtectedPathList(p for p in sys.path if "amdi-os" not in p)

# Resolve absolute paths
root_dir = str(Path(__file__).parent.parent.resolve())

# Prioritize the root directory to import from the unified 'src' folder
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
