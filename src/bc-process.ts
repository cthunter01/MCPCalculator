/**
 * BC Process wrapper - manages individual BC calculator process
 * Handles process lifecycle, I/O communication, and error handling
 */

import { spawn, ChildProcess } from 'child_process';
import { BCProcessOptions, BCCalculatorError, BCErrorCode } from './types.js';

interface PendingRequest {
  resolve: (value: string) => void;
  reject: (error: Error) => void;
  timer?: NodeJS.Timeout;
}

export class BCProcess {
  private process: ChildProcess | null = null;
  private isReady: boolean = false;
  private currentPrecision: number;
  private pendingRequest: PendingRequest | null = null;
  private outputBuffer: string = '';
  private errorBuffer: string = '';

  constructor(private options: BCProcessOptions) {
    this.currentPrecision = options.precision;
  }

  /**
   * Start the BC process and initialize it
   */
  async start(): Promise<void> {
    try {
      // Spawn BC with math library (-l flag)
      // Important: shell: false for security - no shell interpretation
      this.process = spawn('bc', ['-l'], {
        shell: false,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      // Set up event handlers
      this.setupHandlers();

      // Wait a moment for process to be ready
      await new Promise(resolve => setTimeout(resolve, 100));

      // Mark as ready before setting precision
      this.isReady = true;

      // Initialize precision using BC's scale variable
      await this.setPrecision(this.options.precision);
    } catch (error) {
      throw new BCCalculatorError(
        `Failed to start BC process: ${error instanceof Error ? error.message : String(error)}`,
        BCErrorCode.BC_SPAWN_ERROR,
        error
      );
    }
  }

  /**
   * Set up event handlers for the BC process
   */
  private setupHandlers(): void {
    if (!this.process) return;

    // Handle stdout - collect calculation results
    this.process.stdout?.on('data', (data: Buffer) => {
      this.outputBuffer += data.toString();
      
      // BC outputs results line by line, ending with newline
      const lines = this.outputBuffer.split('\n');
      
      // If we have at least 2 lines (result + empty), we have a complete result
      if (lines.length >= 2) {
        // Keep the last incomplete line in buffer
        this.outputBuffer = lines.pop() || '';
        
        // Process complete lines (filter out empty lines)
        const results = lines.filter(line => line.trim());
        
        if (results.length > 0 && this.pendingRequest) {
          // Take the last result (most recent)
          const result = results[results.length - 1].trim();
          this.resolvePendingRequest(result);
        }
      }
    });

    // Handle stderr - capture errors from BC
    this.process.stderr?.on('data', (data: Buffer) => {
      const errorText = data.toString().trim();
      this.errorBuffer += errorText + '\n';
      
      // If we have a pending request and get an error, reject it
      if (errorText && this.pendingRequest) {
        this.rejectPendingRequest(
          new BCCalculatorError(
            `BC error: ${errorText}`,
            BCErrorCode.BC_RUNTIME_ERROR
          )
        );
      }
    });

    // Handle process exit
    this.process.on('exit', (code, signal) => {
      this.isReady = false;
      
      if (this.pendingRequest) {
        this.rejectPendingRequest(
          new BCCalculatorError(
            `BC process exited unexpectedly (code: ${code}, signal: ${signal})`,
            BCErrorCode.BC_PROCESS_EXIT,
            { code, signal }
          )
        );
      }
    });

    // Handle process errors
    this.process.on('error', (error) => {
      this.isReady = false;
      
      if (this.pendingRequest) {
        this.rejectPendingRequest(
          new BCCalculatorError(
            `BC process error: ${error.message}`,
            BCErrorCode.BC_SPAWN_ERROR,
            error
          )
        );
      }
    });
  }

  /**
   * Evaluate a mathematical expression using BC
   * @param expression The expression to evaluate (already validated)
   * @param timeout Optional timeout in milliseconds (overrides default)
   * @returns The calculated result as a string
   */
  async evaluate(expression: string, timeout?: number): Promise<string> {
    if (!this.isReady || !this.process || !this.process.stdin) {
      throw new BCCalculatorError(
        'BC process not ready',
        BCErrorCode.BC_NOT_READY
      );
    }

    if (this.pendingRequest) {
      throw new BCCalculatorError(
        'BC process is busy with another calculation',
        BCErrorCode.BC_NOT_READY
      );
    }

    const timeoutMs = timeout ?? this.options.timeout;

    return new Promise((resolve, reject) => {
      this.pendingRequest = { resolve, reject };
      
      // Clear buffers before new calculation
      this.outputBuffer = '';
      this.errorBuffer = '';

      // Set timeout
      this.pendingRequest.timer = setTimeout(() => {
        this.rejectPendingRequest(
          new BCCalculatorError(
            `Calculation timeout after ${timeoutMs}ms`,
            BCErrorCode.BC_TIMEOUT
          )
        );
        // Kill the hung process
        this.kill();
      }, timeoutMs);

      try {
        // Send expression to BC stdin
        // BC expects expressions to end with newline
        this.process!.stdin!.write(expression + '\n');
      } catch (error) {
        this.rejectPendingRequest(
          new BCCalculatorError(
            `Failed to write to BC process: ${error instanceof Error ? error.message : String(error)}`,
            BCErrorCode.INTERNAL_ERROR,
            error
          )
        );
      }
    });
  }

  /**
   * Set the precision (decimal places) for calculations
   * @param scale Number of decimal places (0-100)
   */
  async setPrecision(scale: number): Promise<void> {
    // Validate scale
    if (scale < 0 || scale > 100) {
      throw new BCCalculatorError(
        `Invalid precision: ${scale}. Must be between 0 and 100`,
        BCErrorCode.VALIDATION_ERROR
      );
    }

    // Set scale using BC's scale variable
    await this.evaluate(`scale=${scale}`);
    this.currentPrecision = scale;
  }

  /**
   * Get current precision setting
   */
  getPrecision(): number {
    return this.currentPrecision;
  }

  /**
   * Resolve a pending calculation request
   */
  private resolvePendingRequest(result: string): void {
    if (!this.pendingRequest) return;
    
    const { resolve, timer } = this.pendingRequest;
    if (timer) clearTimeout(timer);
    
    this.pendingRequest = null;
    resolve(result);
  }

  /**
   * Reject a pending calculation request
   */
  private rejectPendingRequest(error: Error): void {
    if (!this.pendingRequest) return;
    
    const { reject, timer } = this.pendingRequest;
    if (timer) clearTimeout(timer);
    
    this.pendingRequest = null;
    reject(error);
  }

  /**
   * Check if the process is available for new calculations
   */
  isAvailable(): boolean {
    return this.isReady && this.pendingRequest === null && this.process !== null;
  }

  /**
   * Kill the BC process
   */
  kill(): void {
    if (this.process) {
      try {
        this.process.kill('SIGTERM');
      } catch (error) {
        // Ignore errors when killing
      }
      this.process = null;
      this.isReady = false;
    }
  }

  /**
   * Get process ID (for debugging)
   */
  getPid(): number | undefined {
    return this.process?.pid;
  }
}