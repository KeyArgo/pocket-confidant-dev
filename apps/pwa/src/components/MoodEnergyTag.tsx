// Compact, one-tap mood + energy tagger that sits under the write textarea.
// Presentational: App owns the values and persists them via addEntry(). Tapping
// the already-selected value clears it (so "no tag" stays cheap and honest).

import type { CSSProperties } from "react";

export interface MoodEnergyTagProps {
  mood: number | null; // 1..5 or null
  energy: number | null; // 1..5 or null
  onChange: (mood: number | null, energy: number | null) => void;
}

// 1..5 from low to high. Emoji read left→right as a gentle gradient.
const MOOD_FACES = ["😔", "🙁", "😐", "🙂", "😄"];
const MOOD_LABELS = ["Heavy", "Low", "Even", "Good", "Light"];
const ENERGY_LABELS = ["Drained", "Tired", "Steady", "Lively", "Charged"];

const ROW_STYLE: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "0.6rem",
  marginTop: "0.5rem",
};
const LABEL_STYLE: CSSProperties = {
  fontSize: "0.8rem",
  color: "var(--muted)",
  width: "3.6rem",
  flexShrink: 0,
};
const DOTS_STYLE: CSSProperties = {
  display: "flex",
  gap: "0.3rem",
};

function dotStyle(on: boolean, emoji: boolean): CSSProperties {
  return {
    cursor: "pointer",
    border: `1px solid ${on ? "var(--accent)" : "var(--line)"}`,
    background: on ? "var(--accent)" : "var(--card)",
    color: on ? "#fff" : "var(--muted)",
    borderRadius: "999px",
    width: emoji ? "2rem" : "1.5rem",
    height: emoji ? "2rem" : "1.5rem",
    fontSize: emoji ? "1.05rem" : "0.7rem",
    lineHeight: 1,
    padding: 0,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.15s",
  };
}

function Scale(props: {
  label: string;
  values: string[];
  itemLabels: string[];
  emoji: boolean;
  selected: number | null;
  onPick: (v: number | null) => void;
}) {
  return (
    <div style={ROW_STYLE}>
      <span style={LABEL_STYLE}>{props.label}</span>
      <div style={DOTS_STYLE} role="group" aria-label={props.label}>
        {props.values.map((glyph, i) => {
          const value = i + 1;
          const on = props.selected === value;
          return (
            <button
              key={value}
              type="button"
              style={dotStyle(on, props.emoji)}
              aria-pressed={on}
              aria-label={`${props.label}: ${props.itemLabels[i]}`}
              title={props.itemLabels[i]}
              // Tap the active value again to clear it.
              onClick={() => props.onPick(on ? null : value)}
            >
              {glyph}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function MoodEnergyTag({
  mood,
  energy,
  onChange,
}: MoodEnergyTagProps) {
  return (
    <div style={{ marginTop: "0.6rem" }}>
      <Scale
        label="Mood"
        values={MOOD_FACES}
        itemLabels={MOOD_LABELS}
        emoji
        selected={mood}
        onPick={(v) => onChange(v, energy)}
      />
      <Scale
        label="Energy"
        values={["1", "2", "3", "4", "5"]}
        itemLabels={ENERGY_LABELS}
        emoji={false}
        selected={energy}
        onPick={(v) => onChange(mood, v)}
      />
    </div>
  );
}
