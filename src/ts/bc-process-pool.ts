/**
 * BC Process Pool Manager
 * Manages a pool of BC processes for concurrent request handling
 */

import { BCProcess } from './bc-process.js';
import { ProcessPoolConfig, BCCalculatorError, BCErrorCode } from './types.js';

export class BCProcessPool {
  private processes: BCProcess[] = [];
  private availableProcesses: BCProcess[] = [];
  private config: ProcessPoolConfig;
  private isInitialized: boolean = false;

  constructor(config: ProcessPoolConfig) {
    this.config = config;
  }

  /**
   * Initialize the process pool by spawning configured number of BC processes
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      console.error('BC process pool already initialized');
      return;
    }

    console.error(`Initializing BC process pool with ${this.config.poolSize} processes...`);

    try {
      // Create pool of processes
      const promises: Promise<BCProcess>[] = [];
      for (let i = 0; i < this.config.poolSize; i++) {
        promises.push(this.createProcess(i));
      }
      
      // Wait for all processes to start
      await Promise.all(promises);
      
      this.isInitialized = true;
      console.error(`BC process pool initialized successfully with ${this.processes.length} processes`);
    } catch (error) {
      console.error(`Failed to initialize BC process pool: ${error}`);
      // Clean up any processes that were created
      await this.shutdown();
      throw new BCCalculatorError(
        `Failed to initialize BC process pool: ${error instanceof Error ? error.message : String(error)}`,
        BCErrorCode.BC_SPAWN_ERROR,
        error
      );
    }
  }

  /**
   * Create and initialize a new BC process
   * @param index Process index for logging
   */
  private async createProcess(index?: number): Promise<BCProcess> {
    const logPrefix = index !== undefined ? `[Process ${index}]` : '[Process]';
    
    try {
      const process = new BCProcess({
        precision: this.config.defaultPrecision,
        timeout: this.config.defaultTimeout,
        useMathLibrary: true
      });
      
      await process.start();
      
      this.processes.push(process);
      this.availableProcesses.push(process);
      
      if (index !== undefined) {
        console.error(`${logPrefix} Started successfully (PID: ${process.getPid()})`);
      }
      
      return process;
    } catch (error) {
      console.error(`${logPrefix} Failed to start: ${error}`);
      throw error;
    }
  }

  /**
   * Acquire a process from the pool
   * Waits if no processes are currently available
   */
  async acquireProcess(): Promise<BCProcess> {
    if (!this.isInitialized) {
      throw new BCCalculatorError(
        'BC process pool not initialized',
        BCErrorCode.BC_NOT_READY
      );
    }

    // Wait for an available process
    const maxWaitTime = 30000; // 30 seconds
    const checkInterval = 100; // Check every 100ms
    let waitedTime = 0;

    while (this.availableProcesses.length === 0 && waitedTime < maxWaitTime) {
      await new Promise(resolve => setTimeout(resolve, checkInterval));
      waitedTime += checkInterval;
    }

    if (this.availableProcesses.length === 0) {
      throw new BCCalculatorError(
        'No BC processes available after waiting',
        BCErrorCode.BC_NOT_READY
      );
    }

    const process = this.availableProcesses.shift()!;
    
    // Verify process is still healthy
    if (!process.isAvailable()) {
      console.error(`Process ${process.getPid()} is not available, attempting recovery`);
      // Process died, create replacement
      process.kill();
      const newProcess = await this.createProcess();
      return newProcess; // New process is already available
    }

    return process;
  }

  /**
   * Release a process back to the pool
   * If the process is unhealthy, it will be replaced
   */
  releaseProcess(process: BCProcess): void {
    if (!this.processes.includes(process)) {
      console.error('Attempted to release process not in pool');
      return;
    }

    if (process.isAvailable()) {
      // Process is healthy, return to available pool
      if (!this.availableProcesses.includes(process)) {
        this.availableProcesses.push(process);
      }
    } else {
      // Process is unhealthy, replace it
      console.error(`Process ${process.getPid()} is unhealthy, replacing...`);
      
      // Remove from both lists
      this.processes = this.processes.filter(p => p !== process);
      this.availableProcesses = this.availableProcesses.filter(p => p !== process);
      
      // Kill the bad process
      process.kill();
      
      // Create replacement (non-blocking)
      this.createProcess().catch(error => {
        console.error(`Failed to create replacement process: ${error}`);
      });
    }
  }

  /**
   * Get the number of available processes
   */
  getAvailableCount(): number {
    return this.availableProcesses.length;
  }

  /**
   * Get the total number of processes in the pool
   */
  getTotalCount(): number {
    return this.processes.length;
  }

  /**
   * Get pool status information
   */
  getStatus(): {
    initialized: boolean;
    totalProcesses: number;
    availableProcesses: number;
    busyProcesses: number;
  } {
    return {
      initialized: this.isInitialized,
      totalProcesses: this.processes.length,
      availableProcesses: this.availableProcesses.length,
      busyProcesses: this.processes.length - this.availableProcesses.length
    };
  }

  /**
   * Shutdown the process pool
   * Kills all BC processes
   */
  async shutdown(): Promise<void> {
    console.error('Shutting down BC process pool...');
    
    for (const process of this.processes) {
  process.kill();
    }
    
    this.processes = [];
    this.availableProcesses = [];
    this.isInitialized = false;
    
    console.error('BC process pool shutdown complete');
  }
}