import { AmdiClient } from "../src";

describe("AmdiClient smoke", () => {
  it("constructs without throwing", () => {
    expect(() => new AmdiClient("localhost:0")).not.toThrow();
  });
});
