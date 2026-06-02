// Free/Pro entitlements — the commercial boundary, kept pure and testable.
//
// Philosophy (per market guidance): the free tier must be genuinely useful and
// non-aggressive. Journaling, on-device reflections, and basic "ask your journal"
// are ALWAYS free — that's the trust-building core of a confidential confidant.
// Pro adds depth features (deep insight tooling, trends, the yearly story,
// data portability conveniences, and at-rest encryption). No payments ship in v1;
// this module only defines the boundary so the UI can gate cleanly.
//
// Pure logic only: persistence is via the injected/imported getMeta/setMeta from
// db.ts (the one allowed store). The pure gating function `isAllowed` takes a tier
// so it stays trivially unit-testable with no DB.

import { getMeta, setMeta } from "../data/db";

export type Tier = "free" | "pro";

// The full feature surface the app gates on. Keep this union small and stable —
// the UI references these string literals when checking access.
export type Feature =
  | "journal" // write entries — always free
  | "reflection" // on-device reflection on an entry — always free
  | "basic-ask" // limited "ask your journal" queries — free
  | "unlimited-ask" // unlimited "ask your journal" — pro
  | "trends" // mood/energy trends + charts — pro
  | "yearly-summary" // the "year in review" narrative — pro
  | "export" // one-tap JSON export of the whole journal — pro
  | "encryption"; // at-rest encryption of text/reflection — pro

const META_KEY = "entitlement:tier";

// Generous free tier: the whole reflective loop works for free, plus a taste of
// "ask your journal". Everything that turns occasional use into a daily habit is
// free; Pro is for depth and convenience, never for the core experience.
const FREE_FEATURES: ReadonlySet<Feature> = new Set<Feature>([
  "journal",
  "reflection",
  "basic-ask",
]);

// Pro is additive: it includes every free feature plus the depth/convenience set.
const PRO_EXTRAS: ReadonlySet<Feature> = new Set<Feature>([
  "unlimited-ask",
  "trends",
  "yearly-summary",
  "export",
  "encryption",
]);

// Display metadata for each feature, so Settings/Paywall can render a consistent,
// honest list without hard-coding copy in components.
export interface FeatureInfo {
  feature: Feature;
  label: string;
  description: string;
}

const FEATURE_INFO: Record<Feature, FeatureInfo> = {
  journal: {
    feature: "journal",
    label: "Private journaling",
    description: "Write as much as you like. Always free.",
  },
  reflection: {
    feature: "reflection",
    label: "On-device reflections",
    description: "A gentle reflection and question after each entry.",
  },
  "basic-ask": {
    feature: "basic-ask",
    label: "Ask your journal",
    description: "Ask questions about your own past entries.",
  },
  "unlimited-ask": {
    feature: "unlimited-ask",
    label: "Unlimited ask",
    description: "Ask your journal as often as you like, without limits.",
  },
  trends: {
    feature: "trends",
    label: "Mood & energy trends",
    description: "See how you've been over time, charted on-device.",
  },
  "yearly-summary": {
    feature: "yearly-summary",
    label: "Your year in review",
    description: "A warm narrative summary of your year, written privately.",
  },
  export: {
    feature: "export",
    label: "Export your journal",
    description: "One-tap export of everything as portable JSON.",
  },
  encryption: {
    feature: "encryption",
    label: "At-rest encryption",
    description: "Encrypt entries on this device with a passphrase.",
  },
};

// The features included at each tier, for display in Settings/Paywall.
// `pro` deliberately lists the additive extras only (free features are shown
// under the free tier), so the UI can present "what Pro adds".
export const FEATURES_BY_TIER: Record<Tier, FeatureInfo[]> = {
  free: [...FREE_FEATURES].map((f) => FEATURE_INFO[f]),
  pro: [...PRO_EXTRAS].map((f) => FEATURE_INFO[f]),
};

/** Pure gate: is `feature` available to a user on `tier`? */
export function isAllowed(feature: Feature, tier: Tier): boolean {
  if (FREE_FEATURES.has(feature)) return true;
  return tier === "pro" && PRO_EXTRAS.has(feature);
}

/** Read the persisted tier (defaults to 'free' on first run / unknown values). */
export async function getTier(): Promise<Tier> {
  const stored = await getMeta<string>(META_KEY);
  return stored === "pro" ? "pro" : "free";
}

/** Persist the user's tier. */
export async function setTier(tier: Tier): Promise<void> {
  await setMeta(META_KEY, tier);
}

/** Human-readable info for a single feature (for Paywall copy). */
export function featureInfo(feature: Feature): FeatureInfo {
  return FEATURE_INFO[feature];
}
