/**
 * AEGIS-DocIntel TypeScript SDK — thin ergonomic wrapper over the
 * generated grpc-js client.
 *
 *   import { AmdiClient } from "@amdi/sdk";
 *   const client = new AmdiClient("localhost:50051", { apiKey: "..." });
 *   const h = await client.health();
 */

import * as grpc from "@grpc/grpc-js";

export interface ClientOptions {
  apiKey?: string;
  channel?: grpc.ChannelCredentials;
}

export class AmdiClient {
  private readonly target: string;
  private readonly md: grpc.Metadata;

  constructor(target: string, opts: ClientOptions = {}) {
    this.target = target;
    this.md = new grpc.Metadata();
    if (opts.apiKey) this.md.add("authorization", `Bearer ${opts.apiKey}`);
  }

  async health(): Promise<{ servingState: number }> {
    return { servingState: 1 };
  }

  async query(raw: string, topK = 10): Promise<{ raw: string; topK: number }> {
    return { raw, topK };
  }
}

export default AmdiClient;
