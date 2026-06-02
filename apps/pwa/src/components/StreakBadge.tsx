// A small, warm, non-punishing streak badge for the masthead.
// Presentational only: it derives everything from `entries` via pure logic in
// features/streaks.ts. No app state, no side effects, never guilt-trips.

import { useMemo } from "react";
import type { Entry } from "../lib/core/types";
import { computeStreak, streakMessage } from "../lib/features/streaks";

export interface StreakBadgeProps {
  entries: Entry[];
}

export default function StreakBadge({ entries }: StreakBadgeProps) {
  const { info, message } = useMemo(() => {
    const i = computeStreak(entries);
    return { info: i, message: streakMessage(i) };
  }, [entries]);

  // A lit flame when journaled today; a soft sparkle when the run is alive on
  // grace/yesterday; a seedling when resting. Never an "X" or warning glyph —
  // resting is okay here.
  const glyph = info.activeToday ? "🔥" : info.current > 0 ? "✨" : "🌱";

  return (
    <div
      className="streak-badge"
      title={message}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.4rem",
        padding: "0.25rem 0.6rem",
        background: "var(--card)",
        border: "1px solid var(--line)",
        borderRadius: "999px",
        color: "var(--muted)",
        fontSize: "0.82rem",
        fontFamily: "var(--sans)",
        lineHeight: 1.2,
      }}
    >
      <span aria-hidden="true" style={{ fontSize: "0.95rem" }}>
        {glyph}
      </span>
      {info.current > 0 && (
        <span
          style={{
            fontWeight: 600,
            color: "var(--accent)",
            fontFamily: "var(--serif)",
          }}
        >
          {info.current}
        </span>
      )}
      <span>{message}</span>
    </div>
  );
}
