"""
Example: using aegis-docprep's PII redaction as a LangChain document
transformer, so sensitive data is scrubbed before it reaches an LLM.
"""

from __future__ import annotations

from typing import List
from langchain_core.documents import Document

from aegis_docprep import apply_redaction_policy, detect_pii


class PIIRedactingTransformer:
    """LangChain Document Transformer that scrubs detected PII entities."""

    def transform_documents(self, documents: List[Document]) -> List[Document]:
        out = []
        for doc in documents:
            entities = detect_pii({"id": doc.metadata.get("id", ""), "text": doc.page_content})
            redacted_text = apply_redaction_policy(doc.page_content, entities)
            out.append(Document(page_content=redacted_text, metadata=doc.metadata))
        return out


if __name__ == "__main__":
    docs = [
        Document(
            page_content="Customer Alice Walker SSN: 123-45-6789 requested billing support.",
            metadata={"source": "support_ticket_1"},
        ),
        Document(
            page_content="Call technician at 555-123-0199 for server maintenance.",
            metadata={"source": "ops_notes"},
        ),
    ]

    transformer = PIIRedactingTransformer()
    redacted_docs = transformer.transform_documents(docs)

    print("Transformed documents successfully:")
    for d in redacted_docs:
        print(f"[{d.metadata['source']}]: {d.page_content}")
