import { describe, expect, it } from "vitest";

import { normalizeRunnerUrl, parsePhoneNumbers } from "../lib/runner-utils";

describe("runner utilities", () => {
  it("normalizes an entered runner URL without its trailing slash", () => {
    expect(normalizeRunnerUrl("  http://192.168.1.10:8787/// ")).toBe("http://192.168.1.10:8787");
  });

  it("parses only non-empty phone-number rows", () => {
    expect(parsePhoneNumbers("+2010\n\n  +2011  \n")).toEqual(["+2010", "+2011"]);
  });
});
