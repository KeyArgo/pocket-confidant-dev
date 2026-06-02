import { describe, it, expect, beforeEach } from "vitest";

// We test the pure gate (`isAllowed`, `FEATURES_BY_TIER`, `featureInfo`) directly,
// and the persisted getTier/setTier against an in-memory stub of the meta store.
// db.ts uses IndexedDB which isn't present under Node, so we mock the two meta
// helpers entitlements depends on.

const metaStore = new Map<string, unknown>();

vi.mock("../../data/db", () => ({
  getMeta: async <T>(key: string): Promise<T | undefined> =>
    metaStore.get(key) as T | undefined,
  setMeta: async (key: string, value: unknown): Promise<void> => {
    metaStore.set(key, value);
  },
}));

import {
  isAllowed,
  getTier,
  setTier,
  FEATURES_BY_TIER,
  featureInfo,
  type Feature,
} from "../entitlements";

beforeEach(() => {
  metaStore.clear();
});

describe("isAllowed — free features", () => {
  const freeFeatures: Feature[] = ["journal", "reflection", "basic-ask"];
  for (const f of freeFeatures) {
    it(`allows ${f} on free`, () => {
      expect(isAllowed(f, "free")).toBe(true);
    });
    it(`allows ${f} on pro`, () => {
      expect(isAllowed(f, "pro")).toBe(true);
    });
  }
});

describe("isAllowed — pro features", () => {
  const proFeatures: Feature[] = [
    "unlimited-ask",
    "trends",
    "yearly-summary",
    "export",
    "encryption",
  ];
  for (const f of proFeatures) {
    it(`blocks ${f} on free`, () => {
      expect(isAllowed(f, "free")).toBe(false);
    });
    it(`allows ${f} on pro`, () => {
      expect(isAllowed(f, "pro")).toBe(true);
    });
  }
});

describe("getTier / setTier", () => {
  it("defaults to free when nothing stored", async () => {
    expect(await getTier()).toBe("free");
  });

  it("defaults to free for an unknown stored value", async () => {
    metaStore.set("entitlement:tier", "garbage");
    expect(await getTier()).toBe("free");
  });

  it("round-trips pro", async () => {
    await setTier("pro");
    expect(await getTier()).toBe("pro");
  });

  it("round-trips back to free", async () => {
    await setTier("pro");
    await setTier("free");
    expect(await getTier()).toBe("free");
  });
});

describe("FEATURES_BY_TIER display data", () => {
  it("free lists the generous free set", () => {
    const labels = FEATURES_BY_TIER.free.map((f) => f.feature);
    expect(labels).toEqual(["journal", "reflection", "basic-ask"]);
  });

  it("pro lists only the additive extras", () => {
    const labels = FEATURES_BY_TIER.pro.map((f) => f.feature);
    expect(labels).toContain("trends");
    expect(labels).toContain("export");
    expect(labels).not.toContain("journal"); // free features not duplicated
  });

  it("every entry carries a label and description", () => {
    for (const info of [...FEATURES_BY_TIER.free, ...FEATURES_BY_TIER.pro]) {
      expect(info.label.length).toBeGreaterThan(0);
      expect(info.description.length).toBeGreaterThan(0);
    }
  });
});

describe("featureInfo", () => {
  it("returns metadata for a feature", () => {
    expect(featureInfo("trends").label).toBe("Mood & energy trends");
  });
});
