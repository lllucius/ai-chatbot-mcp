// Base API response types
export interface BaseResponse {
  success: boolean;
  message?: string;
  timestamp?: string;
}

// Common types
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

export interface SearchParams extends PaginationParams {
  query?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}