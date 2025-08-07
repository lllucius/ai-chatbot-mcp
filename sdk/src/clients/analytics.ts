/**
 * Analytics client for system analytics and reporting
 */

import { HttpClient } from '../http-client';
import { UsageAnalytics } from '../types';

export class AnalyticsClient {
  constructor(private http: HttpClient) {}

  /**
   * Get system overview analytics
   */
  async getOverview(): Promise<any> {
    return this.http.get('/api/v1/analytics/overview');
  }

  /**
   * Get usage analytics
   */
  async getUsage(options: {
    period?: string;
    detailed?: boolean;
  } = {}): Promise<UsageAnalytics> {
    const params = new URLSearchParams();
    
    if (options.period) params.append('period', options.period);
    if (options.detailed !== undefined) params.append('detailed', options.detailed.toString());

    const query = params.toString();
    return this.http.get<UsageAnalytics>(
      `/api/v1/analytics/usage${query ? '?' + query : ''}`
    );
  }

  /**
   * Get performance analytics
   */
  async getPerformance(): Promise<any> {
    return this.http.get('/api/v1/analytics/performance');
  }

  /**
   * Get user analytics
   */
  async getUsersAnalytics(options: {
    top?: number;
    metric?: string;
  } = {}): Promise<any> {
    const params = new URLSearchParams();
    
    if (options.top) params.append('top', options.top.toString());
    if (options.metric) params.append('metric', options.metric);

    const query = params.toString();
    return this.http.get(
      `/api/v1/analytics/users${query ? '?' + query : ''}`
    );
  }

  /**
   * Get trend analytics
   */
  async getTrends(): Promise<any> {
    return this.http.get('/api/v1/analytics/trends');
  }

  /**
   * Export analytics report
   */
  async exportReport(options: {
    output?: string;
    details?: boolean;
  } = {}): Promise<any> {
    return this.http.post('/api/v1/analytics/export-report', options);
  }
}