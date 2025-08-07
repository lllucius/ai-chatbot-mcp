/**
 * Health monitoring client for system status and diagnostics
 */

import { HttpClient } from '../http-client';
import { 
  HealthStatus, 
  DatabaseHealth, 
  ServicesHealth, 
  SystemMetrics,
  BaseResponse
} from '../types';

export class HealthClient {
  constructor(private http: HttpClient) {}

  /**
   * Get basic health status
   */
  async basic(): Promise<BaseResponse> {
    return this.http.get<BaseResponse>('/api/v1/health/');
  }

  /**
   * Get detailed health status including system information
   */
  async detailed(): Promise<any> {
    return this.http.get('/api/v1/health/detailed');
  }

  /**
   * Check database connectivity status
   */
  async database(): Promise<DatabaseHealth> {
    return this.http.get<DatabaseHealth>('/api/v1/health/database');
  }

  /**
   * Check external services status
   */
  async services(): Promise<ServicesHealth> {
    return this.http.get<ServicesHealth>('/api/v1/health/services');
  }

  /**
   * Get system metrics and performance data
   */
  async metrics(): Promise<SystemMetrics> {
    return this.http.get<SystemMetrics>('/api/v1/health/metrics');
  }

  /**
   * Check if the service is ready to accept requests
   */
  async readiness(): Promise<HealthStatus> {
    return this.http.get<HealthStatus>('/api/v1/health/readiness');
  }

  /**
   * Check if the service is alive
   */
  async liveness(): Promise<HealthStatus> {
    return this.http.get<HealthStatus>('/api/v1/health/liveness');
  }

  /**
   * Get performance metrics
   */
  async performance(): Promise<any> {
    return this.http.get('/api/v1/health/performance');
  }

  /**
   * Get comprehensive health check (convenience method)
   */
  async comprehensive(): Promise<{
    basic: BaseResponse;
    detailed: any;
    database: DatabaseHealth;
    services: ServicesHealth;
    metrics: SystemMetrics;
    readiness: HealthStatus;
    liveness: HealthStatus;
  }> {
    const [basic, detailed, database, services, metrics, readiness, liveness] = await Promise.all([
      this.basic(),
      this.detailed(),
      this.database(),
      this.services(),
      this.metrics(),
      this.readiness(),
      this.liveness(),
    ]);

    return {
      basic,
      detailed,
      database,
      services,
      metrics,
      readiness,
      liveness,
    };
  }
}