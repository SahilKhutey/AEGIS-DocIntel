'''
AEGIS-AEL — Markdown Exporter
================================
Converts UEO into markdown formatting optimized for LLMs.
'''
from __future__ import annotations

from src.ael.ueo import UniversalExportObject


class MarkdownExporter:
    @staticmethod
    def export(ueo: UniversalExportObject) -> str:
        lines: list[str] = []
        # Title
        title_text = ueo.document_summary.title or ueo.metadata.document_name
        lines.append(f'# {title_text}')
        lines.append('')
        # Metadata
        lines.append('## Document Metadata')
        lines.append(f'- **Document**: {ueo.metadata.document_name}')
        lines.append(f'- **Pages**: {ueo.metadata.pages}')
        lines.append(f'- **Type**: {ueo.metadata.document_type}')
        lines.append(f'- **Language**: {ueo.metadata.language}')
        lines.append(f'- **Doc ID**: `{ueo.metadata.doc_id}`')
        lines.append('')
        # Query
        lines.append('## Query')
        lines.append(f'> {ueo.query}')
        lines.append('')
        # Summary
        lines.append('## Summary')
        if ueo.document_summary.abstract:
            lines.append(ueo.document_summary.abstract)
        if ueo.document_summary.key_topics:
            lines.append('')
            lines.append('**Key Topics**: ' + ', '.join(ueo.document_summary.key_topics))
        if ueo.document_summary.keywords:
            lines.append('')
            lines.append('**Keywords**: ' + ', '.join(ueo.document_summary.keywords))
        lines.append('')
        # Key Points
        if ueo.key_points:
            lines.append('## Key Findings')
            for i, kp in enumerate(ueo.key_points, start=1):
                cite = f' [p{kp.page}'
                if kp.section:
                    cite += f', §{kp.section}'
                cite += ']'
                lines.append(f'{i}. {kp.text}{cite}')
            lines.append('')
        # Tables
        if ueo.matrix.tables:
            lines.append('## Tables')
            for tbl in ueo.matrix.tables[:5]:
                if isinstance(tbl, dict):
                    tbl_name = tbl.get('name', 'Table')
                    tbl_page = tbl.get('page', '?')
                    lines.append(f'### {tbl_name}')
                    lines.append(f'*Page {tbl_page}*')
                    lines.append('')
                    headers = tbl.get('headers', [])
                    data = tbl.get('data', [])
                    if headers:
                        lines.append('| ' + ' | '.join(str(h) for h in headers) + ' |')
                        lines.append('|' + '|'.join('---' for _ in headers) + '|')
                    for row in data[:20]:
                        lines.append('| ' + ' | '.join(str(c) for c in row) + ' |')
                    if tbl.get('computed_metrics'):
                        lines.append('')
                        lines.append('**Computed metrics:**')
                        for k, v in tbl['computed_metrics'].items():
                            lines.append(f'- {k}: {v}')
                    lines.append('')
        # Graph relationships
        if ueo.graph.key_relationships:
            lines.append('## Key Relationships')
            for rel in ueo.graph.key_relationships[:10]:
                src_val = rel.get('src', '')
                dst_val = rel.get('dst', '')
                type_val = rel.get('type', '')
                lines.append(f'- {src_val} → {dst_val} ({type_val})')
            lines.append('')
        # Templates
        if ueo.template.templates:
            lines.append('## Document Templates')
            for tmpl in ueo.template.templates[:5]:
                tmpl_id = tmpl.get('id', '')
                tmpl_size = tmpl.get('cluster_size', 0)
                lines.append(f'- **{tmpl_id}**: {tmpl_size} pages')
            lines.append('')
        # Citations
        if ueo.citations:
            lines.append('## Citations')
            for i, c in enumerate(ueo.citations[:20], start=1):
                cite = f'[{i}] Page {c.page}'
                if c.section:
                    cite += f', §{c.section}'
                cite += f' (confidence: {c.confidence:.2f})'
                lines.append(cite)
                snippet_text = c.snippet[:150]
                lines.append(f'    {snippet_text}')
            lines.append('')
        # Confidence
        lines.append('## Confidence')
        lines.append(f'- **Overall**: {ueo.confidence.overall:.3f}')
        lines.append(f'- **Semantic**: {ueo.confidence.semantic:.3f}')
        lines.append(f'- **Numerical**: {ueo.confidence.numerical:.3f}')
        lines.append(f'- **Structural**: {ueo.confidence.structural:.3f}')
        lines.append(f'- **Retrieval**: {ueo.confidence.retrieval:.3f}')
        lines.append('')
        return '\n'.join(lines)
