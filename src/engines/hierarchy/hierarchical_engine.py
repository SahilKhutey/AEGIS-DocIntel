"""
AEGIS-AMDI-OS — Hierarchical Coordinate Engine
================================================
H = (p, s, b, l, t)  - Formula §21

Theorem 21.1: The 5-tuple uniquely identifies any token.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterator, List, Dict, Tuple, Any

import numpy as np

from src.engines.coordinate.coordinate_engine import NormalizedCoordinate

logger = logging.getLogger("amdi.math.hierarchy")


@dataclass(frozen=True)
class HierarchicalCoordinate:
    """
    H = (p, s, b, l, t)
    p = page
    s = section
    b = block
    l = line
    t = token index
    """
    p: int      # page
    s: int      # section
    b: int      # block
    l: int      # line
    t: int      # token

    def to_tuple(self) -> Tuple[int, int, int, int, int]:
        return (self.p, self.s, self.b, self.l, self.t)

    def to_path(self) -> str:
        return f"P{self.p}/S{self.s}/B{self.b}/L{self.l}/T{self.t}"

    def parent(self) -> HierarchicalCoordinate:
        return HierarchicalCoordinate(self.p, self.s, self.b, self.l, 0)

    def ancestors(self) -> List[HierarchicalCoordinate]:
        return [
            HierarchicalCoordinate(self.p, self.s, self.b, 0, 0),
            HierarchicalCoordinate(self.p, self.s, 0, 0, 0),
            HierarchicalCoordinate(self.p, 0, 0, 0, 0),
        ]

    def depth(self) -> int:
        return 5

    def __str__(self) -> str:
        return self.to_path()


@dataclass
class HierarchicalNode:
    """Node in the hierarchical document tree."""
    coord: HierarchicalCoordinate
    content: str
    level: int              # 0=page, 1=section, 2=block, 3=line, 4=token
    children: List[HierarchicalNode] = field(default_factory=list)
    parent: HierarchicalNode | None = None
    element_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class HierarchicalEngine:
    """
    Builds and queries the H = (p, s, b, l, t) tree.
    """

    LEVEL_NAMES = ["page", "section", "block", "line", "token"]

    def __init__(self) -> None:
        self.root = HierarchicalNode(
            coord=HierarchicalCoordinate(0, 0, 0, 0, 0),
            content="<document>",
            level=-1,
        )
        self._id_to_node: Dict[str, HierarchicalNode] = {}
        self._coord_to_node: Dict[Tuple[int, Tuple[int, int, int, int, int]], HierarchicalNode] = {}

    # ------------------------------------------------------------------ #
    # Tree construction                                                    #
    # ------------------------------------------------------------------ #

    def build_from_coords(
        self,
        coords: List[NormalizedCoordinate],
        section_assignments: Dict[str, str] | None = None,
    ) -> HierarchicalNode:
        """
        Build hierarchical tree from flat coordinate list.

        Args:
            coords: list of NormalizedCoordinate
            section_assignments: map of element_id → section_name
        """
        section_assignments = section_assignments or {}
        # Keep track of unique section names seen per page to assign indices
        page_sections: Dict[int, List[str]] = {}
        block_counter: Dict[Tuple[int, str], int] = {}
        line_counter: Dict[Tuple[int, str, int], int] = {}

        for c in coords:
            if not c.content:
                continue
            # Determine section
            section_name = section_assignments.get(c.element_id, "default")
            # Counters
            if c.p not in page_sections:
                page_sections[c.p] = []
            if section_name not in page_sections[c.p]:
                page_sections[c.p].append(section_name)
            s_idx = page_sections[c.p].index(section_name)
            
            section_key = (c.p, section_name)
            b_idx = block_counter.get(section_key, 0)
            block_counter[section_key] = b_idx
            
            block_key = (c.p, section_name, b_idx)
            l_idx = line_counter.get(block_key, 0)
            line_counter[block_key] = l_idx

            # Create nodes for each level
            tokens = c.content.split()
            for t_idx, token in enumerate(tokens):
                h = HierarchicalCoordinate(c.p, s_idx, b_idx, l_idx, t_idx)
                node = HierarchicalNode(
                    coord=h, content=token, level=4,
                    element_id=f"{c.element_id}-t{t_idx}" if t_idx > 0 else c.element_id,
                )
                self._add_node(node, c, section_name)
                if t_idx == 0:
                    block_counter[section_key] = b_idx + 1
            line_counter[block_key] = l_idx + 1
        return self.root

    def _add_node(self, token_node: HierarchicalNode, coord: NormalizedCoordinate, section_name: str) -> None:
        """Add token node + all ancestor nodes."""
        p, s, b, l, t = token_node.coord.to_tuple()
        # Page node
        page_key = (0, (p, 0, 0, 0, 0))
        page_node = self._coord_to_node.get(page_key)
        if page_node is None:
            page_node = HierarchicalNode(
                coord=HierarchicalCoordinate(p, 0, 0, 0, 0),
                content=f"Page {p}", level=0,
            )
            self.root.children.append(page_node)
            page_node.parent = self.root
            self._coord_to_node[page_key] = page_node
        # Section node
        section_key = (1, (p, s, 0, 0, 0))
        section_node = self._coord_to_node.get(section_key)
        if section_node is None:
            section_node = HierarchicalNode(
                coord=HierarchicalCoordinate(p, s, 0, 0, 0),
                content=section_name, level=1,
            )
            page_node.children.append(section_node)
            section_node.parent = page_node
            self._coord_to_node[section_key] = section_node
        # Block node
        block_key = (2, (p, s, b, 0, 0))
        block_node = self._coord_to_node.get(block_key)
        if block_node is None:
            block_node = HierarchicalNode(
                coord=HierarchicalCoordinate(p, s, b, 0, 0),
                content=coord.content[:50] + "...", level=2,
                element_id=coord.element_id,
            )
            section_node.children.append(block_node)
            block_node.parent = section_node
            self._coord_to_node[block_key] = block_node
        # Line node
        line_key = (3, (p, s, b, l, 0))
        line_node = self._coord_to_node.get(line_key)
        if line_node is None:
            line_node = HierarchicalNode(
                coord=HierarchicalCoordinate(p, s, b, l, 0),
                content=coord.content[:80], level=3,
            )
            block_node.children.append(line_node)
            line_node.parent = block_node
            self._coord_to_node[line_key] = line_node
        # Token node
        token_key = (4, token_node.coord.to_tuple())
        line_node.children.append(token_node)
        token_node.parent = line_node
        self._coord_to_node[token_key] = token_node
        self._id_to_node[token_node.element_id] = token_node

    # ------------------------------------------------------------------ #
    # Queries                                                              #
    # ------------------------------------------------------------------ #

    def query(
        self,
        page: int | None = None,
        section: int | None = None,
        block: int | None = None,
        line: int | None = None,
    ) -> List[HierarchicalNode]:
        """Query by partial H = (p, s, b, l, t)."""
        results = []
        for key, node in self._coord_to_node.items():
            level, (p, s, b, l, t) = key
            if page is not None and p != page: continue
            if section is not None and s != section: continue
            if block is not None and b != block: continue
            if line is not None and l != line: continue
            results.append(node)
        return results

    def get_path(self, coord: HierarchicalCoordinate) -> List[HierarchicalNode]:
        """Get the full ancestor path of a coordinate."""
        p, s, b, l, t = coord.to_tuple()
        path = []
        # Page (level 0)
        page_node = self._coord_to_node.get((0, (p, 0, 0, 0, 0)))
        if page_node: path.append(page_node)
        # Section (level 1)
        section_node = self._coord_to_node.get((1, (p, s, 0, 0, 0)))
        if section_node: path.append(section_node)
        # Block (level 2)
        block_node = self._coord_to_node.get((2, (p, s, b, 0, 0)))
        if block_node: path.append(block_node)
        # Line (level 3)
        line_node = self._coord_to_node.get((3, (p, s, b, l, 0)))
        if line_node: path.append(line_node)
        # Token/Target (level 4)
        target_node = self._coord_to_node.get((4, (p, s, b, l, t)))
        if target_node: path.append(target_node)
        return path

    def statistics(self) -> Dict[str, int]:
        return {
            "total_nodes": len(self._coord_to_node),
            "pages": len([n for n in self._coord_to_node.values() if n.level == 0]),
            "sections": len([n for n in self._coord_to_node.values() if n.level == 1]),
            "blocks": len([n for n in self._coord_to_node.values() if n.level == 2]),
            "lines": len([n for n in self._coord_to_node.values() if n.level == 3]),
            "tokens": len([n for n in self._coord_to_node.values() if n.level == 4]),
        }
