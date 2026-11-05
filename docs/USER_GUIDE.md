# User Guide

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

## 1. Getting Started
Users interact with AEGIS-DocIntel through the modern web dashboard or REST APIs.

### Ingesting a Document
1. Navigate to `/dashboard/documents`.
2. Click **Upload Document** and select a PDF file.
3. The system assigns a unique document ID, computes a SHA-256 checksum, and initiates pipeline processing.

### Querying Documents
1. Navigate to `/dashboard/intelligence`.
2. Select your target document or entire corpus.
3. Submit a natural language question.
4. Review the answer along with highlighted optical bounding boxes and page citations.
