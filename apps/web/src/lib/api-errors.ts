export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
    public path?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function mapLoginError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 503) {
      return "The business system is temporarily unavailable. Please try again in a few minutes.";
    }
    if (err.status === 401) {
      if (err.message.toLowerCase().includes("recovery")) {
        return "That recovery key is not valid.";
      }
      return "Email or password is incorrect.";
    }
    if (err.status === 400) {
      return err.message || "This account cannot sign in.";
    }
    if (err.status === 429) {
      return "Too many attempts. Please wait a moment and try again.";
    }
    return "Unable to sign in right now. Please try again.";
  }
  return "Unable to sign in. Check your connection and try again.";
}

export function parseApiError(status: number, body: string): ApiError {
  let message = `Request failed (${status})`;
  try {
    const data = JSON.parse(body) as { detail?: string | { msg?: string }[] };
    if (typeof data.detail === "string") {
      message = data.detail;
    } else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      message = data.detail[0].msg;
    }
  } catch {
    if (body && body.length < 200) message = body;
  }
  return new ApiError(message, status);
}