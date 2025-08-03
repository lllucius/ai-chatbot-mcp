# API Response Patterns

This document describes the API response patterns used in the AI Chatbot MCP application.

## Overview

The application uses two main response patterns:

1. **Wrapped Responses**: `{ success: boolean, message: string, data: T }`
2. **Direct Responses**: `T` (where T is the actual data structure)

## Response Types

### 1. Wrapped Responses (APIResponse<T>)

Used for endpoints that return a single data object wrapped in a success envelope.

**Structure:**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    // Actual data object
  }
}
```

**Examples:**
- `/auth/me` - Returns `APIResponse<User>`
- `/auth/register` - Returns `APIResponse<User>`

### 2. Direct Responses

Used for endpoints that return the data directly, often for complex structures like paginated results.

**Structure:**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "items": [...],
  "pagination": {...}
}
```

**Examples:**
- `/conversations/` - Returns `PaginatedResponse<Conversation>`
- Most collection endpoints with pagination

## Frontend Handling

The frontend API service includes utility functions to handle both patterns:

### extractApiResponseData<T>()
Flexible function that handles both wrapped and direct responses automatically.

```typescript
// Works with both patterns
const data = extractApiResponseData(response, 'Operation name');
```

### extractWrappedApiResponseData<T>()
Strict function for endpoints that must return wrapped responses.

```typescript
// Only works with wrapped responses
const data = extractWrappedApiResponseData(response, 'Operation name');
```

## Guidelines for Developers

### Backend Endpoints

1. **Authentication endpoints**: Use `APIResponse<T>` wrapper
2. **Single object returns**: Use `APIResponse<T>` wrapper
3. **Paginated collections**: Use `PaginatedResponse<T>` directly
4. **Complex structures**: Use appropriate response type directly

### Frontend API Calls

1. **New endpoints**: Use `extractApiResponseData()` for flexibility
2. **Known wrapped endpoints**: Use `extractWrappedApiResponseData()` for strict validation
3. **Update TypeScript types**: Match the actual backend response structure

## Migration Notes

- Authentication endpoints were updated in PR #XX to use wrapped responses
- Existing collection endpoints continue to use direct responses for consistency
- The frontend now gracefully handles both patterns

## Error Handling

Both utility functions provide detailed error logging when response structures don't match expectations, including:
- Response status information
- Available data keys
- Expected vs actual structure

This helps with debugging API response issues during development.