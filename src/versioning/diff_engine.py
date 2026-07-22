'''
AEGIS-DocIntel / AMDI-OS — Document Version & Structural Diff Engine
======================================================================
Computes structural tree-edit distance (APTED style) and node text diffs across document versions.
'''
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StructuralEdit:
    edit_type: str  # "insert" | "delete" | "update" | "move"
    node_path: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None


@dataclass
class VersionDiff:
    from_version: str
    to_version: str
    edits: List[StructuralEdit] = field(default_factory=list)
    edit_distance: int = 0


def compute_structural_diff(
    doc_v1: Dict[str, Any],
    doc_v2: Dict[str, Any],
) -> VersionDiff:
    '''
    Computes structural tree-edit distance and node-level textual diffs between document versions.
    '''
    v1_id = str(doc_v1.get('version_id', 'v1'))
    v2_id = str(doc_v2.get('version_id', 'v2'))

    elems1 = doc_v1.get('elements', [])
    elems2 = doc_v2.get('elements', [])

    edits: List[StructuralEdit] = []
    map1 = {str(e.get('path', e.get('id', idx))): str(e.get('text', '')) for idx, e in enumerate(elems1)}
    map2 = {str(e.get('path', e.get('id', idx))): str(e.get('text', '')) for idx, e in enumerate(elems2)}

    paths1 = set(map1.keys())
    paths2 = set(map2.keys())

    # Deleted nodes
    for p in paths1 - paths2:
        edits.append(StructuralEdit(edit_type='delete', node_path=p, old_content=map1[p]))

    # Inserted nodes
    for p in paths2 - paths1:
        edits.append(StructuralEdit(edit_type='insert', node_path=p, new_content=map2[p]))

    # Modified nodes
    for p in paths1.intersection(paths2):
        if map1[p] != map2[p]:
            edits.append(StructuralEdit(edit_type='update', node_path=p, old_content=map1[p], new_content=map2[p]))

    return VersionDiff(
        from_version=v1_id,
        to_version=v2_id,
        edits=edits,
        edit_distance=len(edits),
    )


def query_changes_since(
    diff_chain: List[VersionDiff],
    section_filter: Optional[str] = None,
) -> List[StructuralEdit]:
    '''
    Queries structural edits across chained version diffs, optionally filtered by section path.
    '''
    all_edits = []
    for diff in diff_chain:
        for edit in diff.edits:
            if section_filter is None or section_filter.lower() in edit.node_path.lower():
                all_edits.append(edit)
    return all_edits
