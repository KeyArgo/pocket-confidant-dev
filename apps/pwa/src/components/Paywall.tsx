// Paywall — a gentle, dismissible upsell shown when a free user reaches a Pro
// feature. Deliberately NOT a dark pattern: it explains the value plainly, the
// close affordance is obvious and equal-weight, and "maybe later" always works.
// Payments don't ship in v1, so the call-to-action is an honest "coming soon".

import { featureInfo, type Feature } from "../lib/features/entitlements";

export interface PaywallProps {
  feature: string; // the Feature literal the user reached (e.g. 'trends')
  onClose: () => void;
  onUpgrade: () => void;
}

// Best-effort lookup: if the caller passes a known Feature literal we can show
// tailored copy; otherwise fall back to neutral wording.
function describe(feature: string): { label: string; description: string } {
  const known: Feature[] = [
    "journal",
    "reflection",
    "basic-ask",
    "unlimited-ask",
    "trends",
    "yearly-summary",
    "export",
    "encryption",
  ];
  if ((known as string[]).includes(feature)) {
    const info = featureInfo(feature as Feature);
    return { label: info.label, description: info.description };
  }
  return { label: "This feature", description: "" };
}

export default function Paywall({ feature, onClose, onUpgrade }: PaywallProps) {
  const { label, description } = describe(feature);

  return (
    <div
      className="paywall-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label={`${label} is a Pocket Confidant Pro feature`}
      onClick={onClose}
    >
      <div className="card paywall-card" onClick={(e) => e.stopPropagation()}>
        <p className="chip" style={{ alignSelf: "flex-start" }}>
          Pocket Confidant Pro
        </p>
        <h2 style={{ fontFamily: "var(--serif)", margin: "0.4rem 0 0.3rem" }}>
          {label}
        </h2>
        {description && (
          <p className="reflection" style={{ marginTop: 0 }}>
            {description}
          </p>
        )}
        <p className="hint">
          Your journaling, reflections, and asking your journal stay free,
          always. Pro just adds a little more depth when you want it.
        </p>

        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            marginTop: "1rem",
            flexWrap: "wrap",
          }}
        >
          <button className="primary" onClick={onUpgrade}>
            Learn about Pro (coming soon)
          </button>
          <button className="quiet" onClick={onClose}>
            Maybe later
          </button>
        </div>
      </div>
    </div>
  );
}
