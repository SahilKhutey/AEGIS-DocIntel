"""
Shared Formatting Helpers
========================

Common formatting functions used by all exporters.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def format_citation(
    citation: Dict[str, Any],
    style: str = "bracketed",
) -> str:
    """
    Format a single citation.

    Styles:
        - bracketed  : [doc_id, p.N, §section]
        - footnote   : ¹ doc_id, p.N
        - inline     : (doc_id, p.N)
        - apa        : (Author, Year, p.N)
    """
    doc_id = citation.get("doc_id", citation.get("source", ""))
    page = citation.get("page", "?")
    section = citation.get("section", "")
    excerpt = citation.get("excerpt", "")
    author = citation.get("author", "")
    year = citation.get("year", "")

    if style == "bracketed":
        base = f"[{doc_id}"
        if page is not None and page != "?":
            base += f", p.{page}"
        if section:
            base += f", §{section}"
        base += "]"
        if excerpt:
            base += f" {excerpt}"
        return base
    if style == "footnote":
        return f"¹ {doc_id}, p.{page}"
    if style == "inline":
        return f"({doc_id}, p.{page})"
    if style == "apa":
        return f"({author}, {year}, p.{page})"
    return str(citation)


def format_table(
    table: Any,
    headers: Optional[List[str]] = None,
    max_rows: int = 100,
) -> str:
    """
    Format a table as Markdown or text.

    Accepts:
        - dict with 'headers' and 'rows'
        - numpy ndarray
        - list of lists
    """
    import numpy as np
    if isinstance(table, dict):
        headers = table.get("headers", headers or [])
        rows = table.get("rows", [])
    elif isinstance(table, np.ndarray):
        if headers is None:
            headers = [f"col_{i}" for i in range(table.shape[1])]
        rows = table[:max_rows].tolist()
    elif isinstance(table, list):
        rows = table[:max_rows]
        if headers is None and rows and isinstance(rows[0], (list, tuple)):
            headers = [f"col_{i}" for i in range(len(rows[0]))]
    else:
        return str(table)
    if not headers:
        return "\n".join(str(row) for row in rows[:max_rows])
    # markdown table
    lines = []
    lines.append("| " + " | ".join(str(h) for h in headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows[:max_rows]:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def format_metadata(metadata: Dict[str, Any], indent: int = 0) -> str:
    """Format a metadata dict as a YAML-style block."""
    lines = []
    prefix = "  " * indent
    for k, v in metadata.items():
        if isinstance(v, dict):
            lines.append(f"{prefix}{k}:")
            lines.append(format_metadata(v, indent + 1))
        elif isinstance(v, list):
            lines.append(f"{prefix}{k}:")
            for item in v:
                if isinstance(item, dict):
                    lines.append(f"{prefix}  -")
                    lines.append(format_metadata(item, indent + 2))
                else:
                    lines.append(f"{prefix}  - {item}")
        else:
            lines.append(f"{prefix}{k}: {v}")
    return "\n".join(lines)


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to a maximum length, preserving word boundaries."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated + "..."