/**
 * Browser session helpers.
 *
 * The session itself is an HttpOnly cookie (`sc_session`) that JavaScript cannot read.
 * `sc_csrf` is a readable companion cookie: its presence means "signed in" for UI
 * purposes, and its value is echoed in `X-CSRF-Token` on every mutating request.
 */
const CSRF_COOKIE = "sc_csrf";
const LEGACY_TOKEN_KEY = "rmd_auth_token";

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const prefix = `${name}=`;
  for (const part of document.cookie.split(";")) {
    const trimmed = part.trim();
    if (trimmed.startsWith(prefix)) return decodeURIComponent(trimmed.slice(prefix.length));
  }
  return null;
}

export function getCsrfToken(): string | null {
  return readCookie(CSRF_COOKIE);
}

/**
 * Session indicator kept under the historical name so pages can keep their
 * `if (!token) return` guards. It is NOT a credential and is never sent as a bearer token.
 */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  purgeLegacyToken();
  return getCsrfToken();
}

export function purgeLegacyToken() {
  try {
    localStorage.removeItem(LEGACY_TOKEN_KEY);
  } catch {
    /* storage unavailable */
  }
}

export async function clearToken(): Promise<void> {
  purgeLegacyToken();
  try {
    await fetch("/api/v1/auth/logout", { method: "POST", credentials: "same-origin" });
  } catch {
    /* offline: cookies expire on their own */
  }
}
