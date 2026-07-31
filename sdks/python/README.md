# AEGIS-DocIntel Python SDK (`amdi-sdk`)

Sync and async gRPC client for AEGIS-DocIntel.

```python
from amdi_sdk import AmdiClient

client = AmdiClient("localhost:50051", api_key="...")
health = client.health()
print(health.version)
```
