export class AmdiError extends Error {
  constructor(message: string, public statusCode?: number, public response?: any) {
    super(message);
    this.name = "AmdiError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class AmdiAuthError extends AmdiError {
  constructor(message: string, statusCode?: number, response?: any) {
    super(message, statusCode, response);
    this.name = "AmdiAuthError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class AmdiNotFoundError extends AmdiError {
  constructor(message: string, statusCode?: number, response?: any) {
    super(message, statusCode, response);
    this.name = "AmdiNotFoundError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class AmdiValidationError extends AmdiError {
  constructor(message: string, statusCode?: number, response?: any) {
    super(message, statusCode, response);
    this.name = "AmdiValidationError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class AmdiRateLimitError extends AmdiError {
  constructor(message: string, public retryAfter?: number, statusCode?: number, response?: any) {
    super(message, statusCode, response);
    this.name = "AmdiRateLimitError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class AmdiServerError extends AmdiError {
  constructor(message: string, statusCode?: number, response?: any) {
    super(message, statusCode, response);
    this.name = "AmdiServerError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class AmdiTimeoutError extends AmdiError {
  constructor(message: string) {
    super(message);
    this.name = "AmdiTimeoutError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
