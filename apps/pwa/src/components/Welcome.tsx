// First-run onboarding hero. Nails the positioning — a confidential AI partner
// for self-understanding, not a journaling app — sets expectations about the
// one-time on-device model download, and surfaces the "ask your journal" hook.
// Presentational only: the integrator owns the onBegin transition + run-once flag.

export interface WelcomeProps {
  /** Called when the user is ready to move on to model setup / writing. */
  onBegin: () => void;
  /** Whether this browser exposes WebGPU (gates the on-device reflections promise). */
  webgpu: boolean;
}

export default function Welcome({ onBegin, webgpu }: WelcomeProps) {
  return (
    <section className="card welcome">
      <p className="welcome-eyebrow">A confidential AI for self-understanding</p>
      <h2 className="welcome-hero">
        Your private mind, understood.
      </h2>
      <p className="welcome-lede">
        Pocket Confidant is an AI that remembers you and reflects with you — and it
        runs <strong>100% on your device</strong>. No account, no cloud, no servers.
        Nothing you write ever leaves this device.
      </p>

      <ul className="welcome-points">
        <li>
          <span className="welcome-ic" aria-hidden="true">🔒</span>
          <span>
            <strong>Truly private.</strong> Everything stays in this browser, encrypted
            on your own hardware. Not even we can read it.
          </span>
        </li>
        <li>
          <span className="welcome-ic" aria-hidden="true">🧠</span>
          <span>
            <strong>It remembers.</strong> The more you share, the better it reflects —
            connecting today back to what you said weeks ago.
          </span>
        </li>
        <li>
          <span className="welcome-ic" aria-hidden="true">💬</span>
          <span>
            <strong>Ask your journal anything.</strong> “When did I last feel like
            this?” — answered privately, only from your own past.
          </span>
        </li>
        <li>
          <span className="welcome-ic" aria-hidden="true">🔌</span>
          <span>
            <strong>Works offline.</strong> A small AI model downloads once, then it’s
            yours forever — instant and offline.
          </span>
        </li>
      </ul>

      {!webgpu && (
        <p className="hint">
          This browser has no WebGPU, so AI reflections are off here — but private
          journaling and “ask your journal” still work fully on-device. For the full
          experience, open Pocket Confidant in a recent Chrome, Edge, or Safari.
        </p>
      )}

      <button className="primary welcome-cta" onClick={onBegin}>
        Begin
      </button>
      <p className="hint welcome-fine">
        The first setup downloads a small model once. After that, everything is
        instant and offline.
      </p>
    </section>
  );
}
