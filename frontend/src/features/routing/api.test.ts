import { describe, expect, it } from "vitest";

import { inquiryFileName } from "./api";

describe("inquiryFileName", () => {
  it("używa numeru sprawy", () => {
    expect(inquiryFileName("UDIP.1435.6.2026")).toBe("zapytanie-UDIP.1435.6.2026.txt");
  });

  it("zamienia znaki spoza nazw plików na myślniki", () => {
    expect(inquiryFileName("UDIP/1435 6/2026")).toBe("zapytanie-UDIP-1435-6-2026.txt");
  });

  it("nie zostawia myślników na brzegach", () => {
    expect(inquiryFileName("  UDIP.1.2026  ")).toBe("zapytanie-UDIP.1.2026.txt");
  });

  it("radzi sobie z pustym numerem", () => {
    expect(inquiryFileName("")).toBe("zapytanie-sprawa.txt");
    expect(inquiryFileName("///")).toBe("zapytanie-sprawa.txt");
  });
});
