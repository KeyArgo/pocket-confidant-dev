// Polished download-progress UX for the one-time on-device model fetch.
// Presentational only — the integrator owns model lifecycle (startModel) and
// passes pct/msg/error down. Mirrors the existing inline loader's states:
//   idle (pct === 0, no error) → show the call-to-action
//   downloading (pct > 0)      → show the progress bar + honest status
//   error                      → show the (graceful, journaling-still-works) note

export interface ModelLoaderProps {
  /** Download/init progress, 0–100. */
  pct: number;
  /** Human-readable status text from the loader (e.g. "Fetching weights…"). */
  msg: string;
  /** Non-null when setup failed or WebGPU is unavailable. */
  error: string | null;
  /** Kick off the one-time model download. */
  onStart: () => void;
  /** Whether this browser exposes WebGPU. */
  webgpu: boolean;
}

export default function ModelLoader({
  pct,
  msg,
  error,
  onStart,
  webgpu,
}: ModelLoaderProps) {
  const downloading = pct > 0 && pct < 100;

  return (
    <section className="card loader">
      {pct === 0 && !error && (
        <>
          <h3 className="loader-title">Set up your private companion</h3>
          <p>
            This downloads a small AI model <strong>once</strong>. After that it’s
            instant, fully offline, and nothing ever leaves this device.
          </p>
          <button className="primary" onClick={onStart}>
            {webgpu ? "Set up (one-time)" : "Continue without reflections"}
          </button>
          <ul className="loader-facts">
            <li>Happens once — then offline forever.</li>
            <li>Resumes automatically if your connection drops.</li>
            <li>
              On a slow connection the first download can take a few minutes. You can
              start writing now while it loads.
            </li>
          </ul>
        </>
      )}

      {downloading && (
        <>
          <h3 className="loader-title">Downloading your model…</h3>
          <div
            className="bar"
            role="progressbar"
            aria-valuenow={pct}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div className="fill" style={{ width: `${pct}%` }} />
          </div>
          <p className="hint">
            {pct}% · {msg || "downloading…"}
          </p>
          <p className="hint">
            Happens once, then offline forever · resumes if interrupted. Feel free to
            start writing while this finishes.
          </p>
        </>
      )}

      {pct >= 100 && !error && (
        <p className="hint">Ready — your companion is set up and offline.</p>
      )}

      {error && <p className="hint error">{error}</p>}
    </section>
  );
}
