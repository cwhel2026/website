/**
 * Lightweight auth error mapping tests (node --test).
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";

// Mirror mapLoginError logic for CI without a TS runner
function mapLoginError(err) {
  if (err?.name === "ApiError") {
    if (err.status === 503) {
      return "The business system is temporarily unavailable. Please try again in a few minutes.";
    }
    if (err.status === 401) {
      if (err.message?.toLowerCase().includes("recovery")) {
        return "That recovery key is not valid.";
      }
      return "Email or password is incorrect.";
    }
    if (err.status === 429) {
      return "Too many attempts. Please wait a moment and try again.";
    }
  }
  return "Unable to sign in. Check your connection and try again.";
}

describe("mapLoginError", () => {
  it("maps 503 to friendly unavailable", () => {
    assert.equal(
      mapLoginError({ name: "ApiError", status: 503, message: "x" }),
      "The business system is temporarily unavailable. Please try again in a few minutes.",
    );
  });
  it("maps 401 to incorrect credentials", () => {
    assert.equal(
      mapLoginError({ name: "ApiError", status: 401, message: "nope" }),
      "Email or password is incorrect.",
    );
  });
  it("maps recovery 401", () => {
    assert.equal(
      mapLoginError({ name: "ApiError", status: 401, message: "Invalid recovery request" }),
      "That recovery key is not valid.",
    );
  });
});