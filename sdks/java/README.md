# AEGIS-DocIntel Java SDK (`io.amdi:amdi-sdk`)

Java client for AEGIS-DocIntel gRPC service.

```java
AmdiClient client = new AmdiClient("localhost:50051", "api-key");
HealthResponse health = client.health();
```
