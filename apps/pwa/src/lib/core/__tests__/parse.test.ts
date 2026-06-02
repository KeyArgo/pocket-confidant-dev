import { describe, it, expect } from "vitest";
import { stripThinking, extractJson, asString } from "../parse";

describe("stripThinking", () => {
  it("removes <think> blocks", () => {
    expect(stripThinking("<think>hmm</think>hello")).toBe("hello");
  });
  it("leaves clean text untouched", () => {
    expect(stripThinking("just text")).toBe("just text");
  });
});

describe("extractJson", () => {
  it("parses a bare object", () => {
    const o = extractJson('{"reflection":"a","question":"b","callback":""}');
    expect(o).toEqual({ reflection: "a", question: "b", callback: "" });
  });
  it("parses a fenced ```json block", () => {
    const o = extractJson('```json\n{"reflection":"x"}\n```');
    expect(o).toEqual({ reflection: "x" });
  });
  it("recovers an object wrapped in prose", () => {
    const o = extractJson('Sure! {"question":"q"} hope that helps');
    expect(o).toEqual({ question: "q" });
  });
  it("strips <think> then parses", () => {
    const o = extractJson('<think>reasoning</think>{"callback":"c"}');
    expect(o).toEqual({ callback: "c" });
  });
  it("handles nested braces via balance matching", () => {
    const o = extractJson('{"a":{"b":1},"c":2}');
    expect(o).toEqual({ a: { b: 1 }, c: 2 });
  });
  it("returns null when there is no object", () => {
    expect(extractJson("no json here")).toBeNull();
  });
});

describe("asString", () => {
  it("coerces and falls back", () => {
    expect(asString(undefined, "x")).toBe("x");
    expect(asString(5)).toBe("5");
    expect(asString("hi")).toBe("hi");
  });
});
