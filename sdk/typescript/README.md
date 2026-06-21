# AMDI-OS TypeScript SDK

Official TypeScript client for the **Adaptive Mathematical Document Intelligence Operating System**.

## Installation

```bash
npm install amdi-os
```

## Quick Start

```typescript
import { AmdiClient } from 'amdi-os';
import * as fs from 'fs';

async function run() {
  // Initialize client
  const client = new AmdiClient('your-api-key', 'https://api.amdi-os.com');

  // 1. Upload a document
  const fileStream = fs.createReadStream('contract.pdf');
  const doc = await client.documents.upload(fileStream, 'contract.pdf', ['financial']);
  console.log(`Uploaded document: ${doc.document_id}`);

  // 2. Hybrid search query
  const results = await client.retrieval.search('What is quantum entanglement?', {
    top_k: 5
  });

  // 3. Compile context report
  const ueo = await client.context.build(
    results.hits.map(h => ({
      candidate_id: h.doc_id,
      content: h.snippet,
      relevance: h.fused_score
    })),
    4000
  );

  // 4. Send context report to agent
  const response = await client.agents.claude.sendUeo(ueo, 'Summarize findings');
  console.log(response.text);
}

run().catch(console.error);
```
