import { describe, expect, it } from "vitest";

import {
  MODE_LABEL,
  MODULE_DESCRIPTIONS,
  describeModule,
} from "@/features/settings/modules";

const MODULES = [
  "cases",
  "ingest",
  "archive",
  "routing",
  "drafting",
  "anonymize",
  "inference",
  "audit",
];

describe("describeModule", () => {
  it("opisuje każdy moduł zgłaszany przez backend", () => {
    for (const name of MODULES) {
      const description = describeModule(name);
      expect(description.label).not.toBe(name);
      expect(description.fake.length).toBeGreaterThan(10);
      expect(description.real.length).toBeGreaterThan(10);
    }
  });

  it("dla nieznanego modułu zwraca nazwę i opis ogólny", () => {
    const description = describeModule("nowy_modul");
    expect(description.label).toBe("nowy_modul");
    expect(description.fake).toContain("demonstracyjne");
    expect(description.real.length).toBeGreaterThan(10);
  });

  it("ma etykiety obu trybów pracy", () => {
    expect(MODE_LABEL.fake).toBe("Atrapa");
    expect(MODE_LABEL.real).toBe("Realny");
  });

  it("nie powtarza nazw modułów", () => {
    const labels = Object.values(MODULE_DESCRIPTIONS).map((entry) => entry.label);
    expect(new Set(labels).size).toBe(labels.length);
  });
});
