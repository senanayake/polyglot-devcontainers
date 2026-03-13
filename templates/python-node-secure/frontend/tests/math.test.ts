import { describe, expect, it } from "vitest";

import { multiply } from "../src/math.js";

describe("multiply", () => {
  it("multiplies two numbers", () => {
    expect(multiply(2, 3)).toBe(6);
  });
});
