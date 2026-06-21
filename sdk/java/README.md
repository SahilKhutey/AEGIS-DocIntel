# AMDI-OS Java SDK

Official Java client for the **Adaptive Mathematical Document Intelligence Operating System**.

## Installation

Add this dependency to your `pom.xml`:

```xml
<dependency>
    <groupId>com.amdi</groupId>
    <artifactId>amdi-os</artifactId>
    <version>1.0.0</version>
</dependency>
```

## Quick Start

```java
import com.amdi.os.AmdiClient;
import com.amdi.os.AmdiModels;
import java.nio.file.Paths;

public class Main {
    public static void main(String[] args) {
        // Initialize client
        AmdiClient client = new AmdiClient("your-api-key", "https://api.amdi-os.com");

        // 1. Upload a document
        AmdiModels.DocumentSummary doc = client.documents.upload(Paths.get("contract.pdf"));
        System.out.println("Uploaded document ID: " + doc.document_id);

        // 2. Hybrid search query
        AmdiModels.RetrievalResult results = client.retrieval.search("What is quantum entanglement?", 10);

        // 3. Send query response verification
        AmdiModels.VerificationReport report = client.verification.verify("The result is entangled.");
        System.out.println("Verification score: " + report.confidence);
    }
}
```
