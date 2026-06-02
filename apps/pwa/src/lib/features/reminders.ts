// Sparse, opt-in local reminders. Dependency-free, on-device only.
//
// Philosophy (mirrors the streak design): we never nag. A reminder fires AT MOST
// once or twice a week — never daily — and only if the user opted in. Everything
// degrades to a graceful no-op when notifications are unsupported or denied.
//
// HOW IT WORKS (and why it's sparse):
// There is no reliable cross-browser "wake me at 9am next Tuesday" web API. We
// therefore use an opportunistic model: whenever the app is open (a tab focus or
// a Service Worker wake), `maybeNotify()` checks whether it is (a) at/after the
// user's preferred hour, (b) a "due" day, and (c) we haven't already fired this
// week. "Due" days are spaced so we fire at most twice in any 7-day window. State
// lives in `getMeta/setMeta` so it persists across sessions/devices-as-one.
//
// iOS / SAFARI LIMITATIONS (documented per assignment):
// - On iOS, the Notifications API only works in a Home-Screen-installed PWA
//   (standalone display mode), iOS 16.4+. In a normal Safari tab it is absent;
//   `requestPermission` will report unsupported and we no-op.
// - iOS does not run Service Workers in the background on a schedule; there is no
//   Background Sync / Periodic Background Sync. So reminders only surface while
//   the PWA is actually open (or briefly woken). This is a platform limit, not a
//   bug — our opportunistic model is the only thing that works everywhere.
// - Permission must be requested from a user gesture (the Settings toggle).

import { getMeta, setMeta } from "../data/db";

const META_PREFS = "reminders.prefs";
const META_LAST_FIRED = "reminders.lastFired"; // 'YYYY-MM-DD' of last notification

export interface ReminderPrefs {
  enabled: boolean;
  preferredHour: number; // 0-23, local time
}

const DEFAULT_PREFS: ReminderPrefs = { enabled: false, preferredHour: 9 };

/** At most ~2 reminders/week: only these weekday indexes are "due". */
const DUE_WEEKDAYS = [1, 4]; // Monday & Thursday (0=Sun … 6=Sat)
const MIN_GAP_DAYS = 2; // never two reminders within this many days

const MS_PER_DAY = 86_400_000;

/** True when the Notifications API exists in this context. */
export function isSupported(): boolean {
  return typeof window !== "undefined" && "Notification" in window;
}

/** Current permission state, or 'unsupported'. */
export function permissionState(): NotificationPermission | "unsupported" {
  if (!isSupported()) return "unsupported";
  return Notification.permission;
}

/** Load persisted prefs (with defaults). */
export async function getPrefs(): Promise<ReminderPrefs> {
  const saved = await getMeta<ReminderPrefs>(META_PREFS);
  return { ...DEFAULT_PREFS, ...(saved ?? {}) };
}

/**
 * Ask the user for notification permission. MUST be called from a user gesture
 * (e.g. the Settings toggle click). Returns the resulting permission, or
 * 'unsupported' when notifications aren't available (e.g. plain iOS Safari).
 */
export async function requestPermission(): Promise<
  NotificationPermission | "unsupported"
> {
  if (!isSupported()) return "unsupported";
  try {
    // Some browsers return a promise; older ones use a callback. Normalize.
    const result = await Notification.requestPermission();
    return result;
  } catch {
    return Notification.permission;
  }
}

/**
 * Enable reminders at a preferred hour. Requests permission if needed and
 * persists prefs. Returns true if reminders are now active (permission granted),
 * false otherwise (denied / unsupported) — caller can reflect this in the UI.
 *
 * NOTE: this does NOT immediately fire anything; reminders surface later via
 * `maybeNotify()` when the app is open on a due day at/after the chosen hour.
 */
export async function scheduleReminder(preferredHour: number): Promise<boolean> {
  const hour = clampHour(preferredHour);
  const perm = await requestPermission();
  const granted = perm === "granted";
  await setMeta(META_PREFS, { enabled: granted, preferredHour: hour });
  return granted;
}

/** Turn reminders off (keeps the chosen hour for next time). */
export async function disableReminders(): Promise<void> {
  const prefs = await getPrefs();
  await setMeta(META_PREFS, { ...prefs, enabled: false });
}

/**
 * Opportunistic check — call on app open / SW wake. Fires a single gentle
 * notification when all of these hold:
 *   - reminders enabled & permission granted & supported
 *   - it's a "due" weekday and at/after the preferred hour
 *   - we haven't fired within MIN_GAP_DAYS (hard cap on frequency)
 * Otherwise it's a no-op. Returns true iff a notification was shown.
 *
 * `now` is injectable for tests.
 */
export async function maybeNotify(now: number = Date.now()): Promise<boolean> {
  if (permissionState() !== "granted") return false;

  const prefs = await getPrefs();
  if (!prefs.enabled) return false;

  const when = new Date(now);
  const today = when.toISOString().slice(0, 10);

  if (!DUE_WEEKDAYS.includes(when.getDay())) return false;
  if (when.getHours() < prefs.preferredHour) return false;

  const last = await getMeta<string>(META_LAST_FIRED);
  if (last) {
    const gap = Math.round(
      (Date.parse(`${today}T00:00:00Z`) - Date.parse(`${last}T00:00:00Z`)) /
        MS_PER_DAY,
    );
    if (gap < MIN_GAP_DAYS) return false; // already reminded recently
  }

  const shown = showNotification();
  if (shown) await setMeta(META_LAST_FIRED, today);
  return shown;
}

/** Fire the actual notification (prefers a SW registration if present). */
function showNotification(): boolean {
  if (permissionState() !== "granted") return false;
  const title = "Pocket Confidant";
  const options: NotificationOptions = {
    body: "A quiet moment to check in with yourself, whenever you're ready.",
    tag: "pocket-confidant-checkin", // collapse duplicates
    silent: false,
  };
  try {
    const sw = navigator.serviceWorker?.controller
      ? navigator.serviceWorker
      : null;
    if (sw?.ready) {
      // Best-effort SW path; ignore failure and fall back below.
      sw.ready
        .then((reg) => reg.showNotification(title, options))
        .catch(() => {
          try {
            new Notification(title, options);
          } catch {
            /* no-op */
          }
        });
      return true;
    }
    new Notification(title, options);
    return true;
  } catch {
    return false;
  }
}

function clampHour(h: number): number {
  if (!Number.isFinite(h)) return DEFAULT_PREFS.preferredHour;
  return Math.min(23, Math.max(0, Math.round(h)));
}
