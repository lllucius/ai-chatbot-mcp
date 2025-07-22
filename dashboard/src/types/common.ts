// Base API response types
export interface BaseResponse {
  success: boolean;
  message?: string;
  timestamp?: string;
}

// Common types
export interface PaginationParams {
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface SearchParams extends PaginationParams {
  query?: string;
}

// Paginated response wrapper
export interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}