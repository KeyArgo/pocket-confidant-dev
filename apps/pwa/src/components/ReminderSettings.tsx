// Opt-in reminder controls for the Settings screen. Presentational shell around
// the dependency-free reminders.ts logic. Self-contained: it loads/saves its own
// prefs via reminders.ts (which uses getMeta/setMeta), so the integrator can drop
// it in without wiring extra state.

import { useEffect, useState } from "react";
import {
  getPrefs,
  scheduleReminder,
  disableReminders,
  permissionState,
} from "../lib/features/reminders";

export interface ReminderSettingsProps {}

const HOUR_OPTIONS: { value: number; label: string }[] = [
  { value: 7, label: "7:00 AM" },
  { value: 8, label: "8:00 AM" },
  { value: 9, label: "9:00 AM" },
  { value: 12, label: "12:00 PM" },
  { value: 18, label: "6:00 PM" },
  { value: 20, label: "8:00 PM" },
  { value: 21, label: "9:00 PM" },
];

export default function ReminderSettings(_props: ReminderSettingsProps) {
  const [enabled, setEnabled] = useState(false);
  const [hour, setHour] = useState(9);
  const [supported, setSupported] = useState(true);
  const [denied, setDenied] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let live = true;
    void (async () => {
      const state = permissionState();
      const prefs = await getPrefs();
      if (!live) return;
      setSupported(state !== "unsupported");
      setDenied(state === "denied");
      setEnabled(prefs.enabled && state === "granted");
      setHour(prefs.preferredHour);
    })();
    return () => {
      live = false;
    };
  }, []);

  async function onToggle(next: boolean) {
    setBusy(true);
    try {
      if (next) {
        const ok = await scheduleReminder(hour);
        setEnabled(ok);
        setDenied(!ok && permissionState() === "denied");
      } else {
        await disableReminders();
        setEnabled(false);
      }
    } finally {
      setBusy(false);
    }
  }

  async function onHourChange(next: number) {
    setHour(next);
    if (enabled) {
      // Re-persist the new hour while keeping reminders on.
      setBusy(true);
      try {
        const ok = await scheduleReminder(next);
        setEnabled(ok);
      } finally {
        setBusy(false);
      }
    }
  }

  return (
    <div className="card">
      <strong style={{ fontFamily: "var(--serif)", fontSize: "1.05rem" }}>
        Gentle reminders
      </strong>
      <p className="hint" style={{ marginTop: "0.4rem" }}>
        A soft nudge once or twice a week — never daily, never a guilt trip. You
        can turn this off anytime. Reminders stay entirely on this device.
      </p>

      {!supported ? (
        <p className="hint">
          Notifications aren't available in this browser. On iPhone, add Pocket
          Confidant to your Home Screen to enable them.
        </p>
      ) : (
        <>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.6rem",
              margin: "0.5rem 0",
            }}
          >
            <input
              type="checkbox"
              checked={enabled}
              disabled={busy}
              onChange={(e) => void onToggle(e.target.checked)}
              style={{ width: "auto" }}
            />
            <span>Remind me to check in</span>
          </label>

          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.6rem",
              opacity: enabled ? 1 : 0.55,
            }}
          >
            <span className="hint">Preferred time</span>
            <select
              value={hour}
              disabled={!enabled || busy}
              onChange={(e) => void onHourChange(Number(e.target.value))}
              style={{
                background: "var(--card)",
                border: "1px solid var(--line)",
                borderRadius: "8px",
                padding: "0.35rem 0.5rem",
                color: "var(--ink)",
                fontFamily: "var(--sans)",
              }}
            >
              {HOUR_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          {denied && (
            <p className="hint error" style={{ marginTop: "0.5rem" }}>
              Notifications are blocked for this site. Allow them in your browser
              settings to turn reminders on.
            </p>
          )}
        </>
      )}
    </div>
  );
}
