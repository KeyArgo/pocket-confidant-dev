// "Insights" tab. All on-device, all hand-rolled SVG (no chart library). Shows
// the headline pattern, average mood per weekday, and a mood sparkline over
// recent entries. Degrades gracefully: nothing tagged yet -> a friendly nudge.

import type { Entry } from "../lib/core/types";
import {
  moodByWeekday,
  moodOverTime,
  pickInsight,
  taggedCount,
  type WeekdayStat,
  type MoodPoint,
} from "../lib/features/trends";

export interface TrendsProps {
  entries: Entry[];
}

// Mood is 1..5; map onto chart height. Colors stay inside the warm palette.
const MOOD_MIN = 1;
const MOOD_MAX = 5;

function WeekdayBars({ stats }: { stats: WeekdayStat[] }) {
  const W = 320;
  const H = 140;
  const padL = 8;
  const padR = 8;
  const padTop = 8;
  const padBottom = 22;
  const plotW = W - padL - padR;
  const plotH = H - padTop - padBottom;
  const slot = plotW / stats.length;
  const barW = slot * 0.6;

  return (
    <svg
      style={{ width: "100%", height: "auto", display: "block" }}
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label="Average mood by weekday"
      preserveAspectRatio="xMidYMid meet"
    >
      {stats.map((s, i) => {
        const cx = padL + slot * i + slot / 2;
        const x = cx - barW / 2;
        const has = s.avgMood != null;
        const norm = has ? (s.avgMood! - MOOD_MIN) / (MOOD_MAX - MOOD_MIN) : 0;
        const h = has ? Math.max(2, norm * plotH) : 0;
        const y = padTop + (plotH - h);
        return (
          <g key={s.weekday}>
            {has && (
              <rect
                x={x}
                y={y}
                width={barW}
                height={h}
                rx={3}
                fill="var(--accent)"
                opacity={0.85}
              >
                <title>{`${s.label}: ${s.avgMood!.toFixed(1)} (${s.count})`}</title>
              </rect>
            )}
            {!has && (
              <rect
                x={x}
                y={padTop + plotH - 2}
                width={barW}
                height={2}
                rx={1}
                fill="var(--line)"
              />
            )}
            <text
              x={cx}
              y={H - 6}
              textAnchor="middle"
              fontSize="10"
              fill="var(--muted)"
            >
              {s.short}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function MoodLine({ points }: { points: MoodPoint[] }) {
  const W = 320;
  const H = 110;
  const padL = 8;
  const padR = 8;
  const padTop = 10;
  const padBottom = 10;
  const plotW = W - padL - padR;
  const plotH = H - padTop - padBottom;

  const n = points.length;
  const xAt = (i: number) =>
    n <= 1 ? padL + plotW / 2 : padL + (plotW * i) / (n - 1);
  const yAt = (m: number) =>
    padTop + (plotH - ((m - MOOD_MIN) / (MOOD_MAX - MOOD_MIN)) * plotH);

  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xAt(i).toFixed(1)} ${yAt(p.mood).toFixed(1)}`)
    .join(" ");

  return (
    <svg
      style={{ width: "100%", height: "auto", display: "block" }}
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label="Mood over recent entries"
      preserveAspectRatio="xMidYMid meet"
    >
      {/* neutral midline at mood 3 */}
      <line
        x1={padL}
        x2={W - padR}
        y1={yAt(3)}
        y2={yAt(3)}
        stroke="var(--line)"
        strokeWidth={1}
      />
      {n > 1 && (
        <path
          d={path}
          fill="none"
          stroke="var(--accent-2)"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
      {points.map((p, i) => (
        <circle key={p.id} cx={xAt(i)} cy={yAt(p.mood)} r={2.5} fill="var(--accent)">
          <title>{`${p.day}: ${p.mood}`}</title>
        </circle>
      ))}
    </svg>
  );
}

export default function Trends({ entries }: TrendsProps) {
  const tagged = taggedCount(entries);
  const insight = pickInsight(entries);
  const stats = moodByWeekday(entries);
  const line = moodOverTime(entries, 30);

  if (tagged === 0) {
    return (
      <section className="trends">
        <p className="empty">
          Tag a few entries with how you feel and your patterns show up here —
          privately, only on this device.
        </p>
      </section>
    );
  }

  return (
    <section className="trends">
      {insight ? (
        <div className="card">
          <p className="reflection" style={{ color: "var(--accent)", fontStyle: "italic", margin: 0 }}>
            {insight}
          </p>
        </div>
      ) : (
        <p className="hint">
          Keep tagging — a few more entries and your weekly pattern will emerge.
        </p>
      )}

      <div className="card">
        <h3 style={{ fontFamily: "var(--serif)", fontSize: "1rem", margin: "0 0 0.6rem", color: "var(--ink)" }}>Mood by weekday</h3>
        <WeekdayBars stats={stats} />
      </div>

      <div className="card">
        <h3 style={{ fontFamily: "var(--serif)", fontSize: "1rem", margin: "0 0 0.6rem", color: "var(--ink)" }}>
          Mood over your last {line.length} {line.length === 1 ? "entry" : "entries"}
        </h3>
        {line.length > 1 ? (
          <MoodLine points={line} />
        ) : (
          <p className="hint">Tag one more entry to see the trend line.</p>
        )}
      </div>
    </section>
  );
}
