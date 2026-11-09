/**
 * Central API Error hierarchy for AEGIS-DocIntel
 * Standardizes HTTP status codes, correlation IDs, and runtime error semantics.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
    public readonly requestId?: string,
    public readonly rawError?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  get isForbidden(): boolean {
    return this.status === 403;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isConflict(): boolean {
    return this.status === 409;
  }

  get isValidationError(): boolean {
    return this.status === 422;
  }

  get isRateLimited(): boolean {
    return this.status === 429;
  }

  get isServerError(): boolean {
    return this.status >= 500 && this.status < 600;
  }
}

export function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

export function isForbidden(error: unknown): boolean {
  return error instanceof ApiError && error.status === 403;
}

export function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

export function isConflict(error: unknown): boolean {
  return error instanceof ApiError && error.status === 409;
}

export function isValidationError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 422;
}
