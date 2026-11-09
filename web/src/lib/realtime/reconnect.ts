/**
 * Exponential backoff reconnect strategy with full jitter
 */
export interface ReconnectConfig {
  initialDelayMs?: number;
  maxDelayMs?: number;
  factor?: number;
  jitter?: boolean;
}

export class ReconnectStrategy {
  private attempts = 0;
  private readonly initialDelayMs: number;
  private readonly maxDelayMs: number;
  private readonly factor: number;
  private readonly jitter: boolean;

  constructor(config: ReconnectConfig = {}) {
    this.initialDelayMs = config.initialDelayMs ?? 1000;
    this.maxDelayMs = config.maxDelayMs ?? 30000;
    this.factor = config.factor ?? 2;
    this.jitter = config.jitter ?? true;
  }

  getNextDelay(): number {
    const calculated = this.initialDelayMs * Math.pow(this.factor, this.attempts);
    const delay = Math.min(calculated, this.maxDelayMs);
    this.attempts++;

    if (this.jitter) {
      // Full jitter: random between 0 and delay
      return Math.floor(Math.random() * delay);
    }
    return delay;
  }

  reset(): void {
    this.attempts = 0;
  }

  get currentAttempts(): number {
    return this.attempts;
  }
}
