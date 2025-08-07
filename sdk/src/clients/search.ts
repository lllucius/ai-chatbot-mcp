/**
 * Search client for document and content search operations
 */

import { HttpClient } from '../http-client';
import { SearchRequest, SearchResponse } from '../types';

export class SearchClient {
  constructor(private http: HttpClient) {}

  /**
   * Search across documents using various algorithms
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    return this.http.post<SearchResponse>('/api/v1/search/', request);
  }

  /**
   * Find similar document chunks to a given chunk
   */
  async findSimilarChunks(chunkId: number, limit: number = 5): Promise<any> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());

    return this.http.get(`/api/v1/search/similar/${chunkId}?${params}`);
  }

  /**
   * Get search suggestions based on query
   */
  async getSuggestions(query: string, limit: number = 5): Promise<string[]> {
    const params = new URLSearchParams();
    params.append('query', query);
    params.append('limit', limit.toString());

    return this.http.get<string[]>(`/api/v1/search/suggestions?${params}`);
  }

  /**
   * Get user's search history
   */
  async getHistory(limit: number = 10): Promise<any[]> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());

    return this.http.get<any[]>(`/api/v1/search/history?${params}`);
  }

  /**
   * Clear user's search history
   */
  async clearHistory(): Promise<any> {
    return this.http.post('/api/v1/search/clear-history');
  }

  /**
   * Quick vector search (convenience method)
   */
  async vectorSearch(query: string, limit: number = 20): Promise<SearchResponse> {
    return this.search({
      query,
      algorithm: 'vector',
      limit
    });
  }

  /**
   * Quick keyword search (convenience method)
   */
  async keywordSearch(query: string, limit: number = 20): Promise<SearchResponse> {
    return this.search({
      query,
      algorithm: 'bm25',
      limit
    });
  }

  /**
   * Hybrid search combining vector and keyword search (convenience method)
   */
  async hybridSearch(query: string, limit: number = 20): Promise<SearchResponse> {
    return this.search({
      query,
      algorithm: 'hybrid',
      limit
    });
  }
}