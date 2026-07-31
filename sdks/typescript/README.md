# AEGIS-DocIntel TypeScript SDK (`@amdi/sdk`)

TypeScript client for AEGIS-DocIntel gRPC service.

```typescript
import { AmdiClient } from "@amdi/sdk";

const client = new AmdiClient("localhost:50051", { apiKey: "..." });
const health = await client.health();
```
