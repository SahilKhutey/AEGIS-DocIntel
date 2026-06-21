# AMDI-OS Python SDK

Official Python SDK for the **Adaptive Mathematical Document Intelligence Operating System**.

## Installation

```bash
pip install amdi-os
```

## Quick Start

### Synchronous Client

```python
from amdi_os import AmdiClient

# Initialize the client
client = AmdiClient(api_key="your-api-key", base_url="https://api.amdi-os.com")

# 1. Upload a document
doc = client.documents.upload("contract.pdf")
print(f"Uploaded document {doc.document_id}")

# 2. Query the retrieval engine (7-method search)
results = client.retrieval.search(query="What is quantum entanglement?")

# 3. Build optimized context report
ueo = client.context.build_from_retrieval(results, total_budget=4000)

# 4. Generate AI Agent response with UEO
response = client.agents.claude.send_ueo(ueo, question="Summarize key findings.")
print(response.text)
```

### Asynchronous Client

```python
import asyncio
from amdi_os import AsyncAmdiClient

async def main():
    async with AsyncAmdiClient(api_key="your-api-key") as client:
        # Upload
        doc = await client.documents.upload("research.pdf")
        
        # Search
        results = await client.retrieval.search(query="Retrieve SVD calculations")
        
        # Build context
        ueo = await client.context.build_from_retrieval(results, total_budget=3000)
        
        # Query Claude agent
        response = await client.agents.claude.send_ueo(ueo, question="Perform analysis")
        print(response.text)

asyncio.run(main())
```
