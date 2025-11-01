/**
 * Type definitions for BC Calculator MCP Server
 */

export interface CalculationRequest {
  expression: string;
  precision?: number;
  timeout?: number;
}

export interface CalculationResult {
  result: string;
  expression: string;
  precision: number;
  executionTimeMs?: number;
}

export interface ValidationResult {
  valid: boolean;
  error?: string;
  sanitized?: string;
}

export interface BCProcessOptions {
  precision: number;
  timeout: number;
  useMathLibrary: boolean;
}

export interface ProcessPoolConfig {
  poolSize: number;
  defaultPrecision: number;
  defaultTimeout: number;
}

/**
 * Custom error class for BC calculator operations
 */
export class BCCalculatorError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'BCCalculatorError';
  }
}

/**
 * Error codes for BC calculator operations
 */
export enum BCErrorCode {
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  BC_NOT_READY = 'BC_NOT_READY',
  BC_RUNTIME_ERROR = 'BC_RUNTIME_ERROR',
  BC_TIMEOUT = 'BC_TIMEOUT',
  BC_PROCESS_EXIT = 'BC_PROCESS_EXIT',
  BC_SPAWN_ERROR = 'BC_SPAWN_ERROR',
  INTERNAL_ERROR = 'INTERNAL_ERROR'
}