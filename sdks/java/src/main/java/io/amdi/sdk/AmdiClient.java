package io.amdi.sdk;

import io.grpc.*;
import java.util.concurrent.TimeUnit;

public class AmdiClient implements AutoCloseable {
    private final ManagedChannel channel;
    private final Metadata authMd = new Metadata();

    public AmdiClient(String target) {
        this(target, null);
    }

    public AmdiClient(String target, String apiKey) {
        this.channel = Grpc.newChannelBuilder(target, InsecureChannelCredentials.create()).build();
        if (apiKey != null) {
            authMd.put(Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER), "Bearer " + apiKey);
        }
    }

    @Override public void close() throws InterruptedException {
        channel.shutdown().awaitTermination(2, TimeUnit.SECONDS);
    }
}
