// Port of engine/confidant.py _strip_thinking + _extract_json. Small local models
// emit <think> blocks, code fences, and prose around their JSON — this recovers the
// object robustly so the UI always has structured fields.

export function stripThinking(text: string): string {
  return text.replace(/<think>[\s\S]*?<\/think>/g, "").trim();
}

export function extractJson(text: string): Record<string, unknown> | null {
  const cleaned = stripThinking(text);

  // Prefer a fenced ```json { ... } ``` block if present.
  const fenced = cleaned.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
  let candidate: string | null = fenced ? fenced[1] : null;

  // Otherwise, brace-match the first balanced object.
  if (candidate === null) {
    const start = cleaned.indexOf("{");
    if (start === -1) return null;
    let depth = 0;
    for (let i = start; i < cleaned.length; i++) {
      const ch = cleaned[i];
      if (ch === "{") depth++;
      else if (ch === "}") {
        depth--;
        if (depth === 0) {
          candidate = cleaned.slice(start, i + 1);
          break;
        }
      }
    }
  }

  if (candidate === null) return null;
  try {
    return JSON.parse(candidate) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function asString(v: unknown, fallback = ""): string {
  if (v === null || v === undefined) return fallback;
  return String(v);
}
