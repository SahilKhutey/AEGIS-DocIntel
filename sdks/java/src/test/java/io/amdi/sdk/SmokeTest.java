package io.amdi.sdk;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;

class SmokeTest {
    @Test void constructs() {
        assertDoesNotThrow(() -> new AmdiClient("localhost:0"));
    }
}
