# AI Chatbot Platform API Documentation

## Overview

The AI Chatbot Platform provides a comprehensive RESTful API for managing users, conversations, documents, and AI-powered chat interactions. This API supports full CRUD operations, real-time chat, document processing with RAG capabilities, and administrative functions.

**Base URL:** `http://localhost:8000`  
**API Version:** v1  
**Authentication:** JWT Bearer Token

## Table of Contents

1. [Authentication](#authentication)
2. [Users](#users)
3. [Conversations](#conversations)
4. [Documents](#documents)
5. [Search](#search)
6. [Health](#health)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)

## Authentication

### POST /api/v1/auth/register

Register a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com", 
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-01-20T10:30:00Z",
    "updated_at": "2025-01-20T10:30:00Z"
  }
}
```

**Validation Rules:**
- Username: 3-50 characters, alphanumeric, underscore, hyphen only
- Password: Minimum 8 characters, must contain uppercase, lowercase, and digit
- Email: Must be valid email format

### POST /api/v1/auth/login

Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### GET /api/v1/auth/me

Get current user profile (requires authentication).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-01-20T10:30:00Z",
    "updated_at": "2025-01-20T10:30:00Z"
  }
}
```

## Users

### GET /api/v1/users/me

Get current user profile with detailed information.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-01-20T10:30:00Z",
    "updated_at": "2025-01-20T10:30:00Z"
  }
}
```

### PUT /api/v1/users/me

Update current user profile.

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "full_name": "John Smith",
  "is_active": true
}
```

### PUT /api/v1/users/me/password

Change user password.

**Request Body:**
```json
{
  "current_password": "CurrentPassword123!",
  "new_password": "NewSecurePassword456!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password updated successfully"
}
```

### GET /api/v1/users (Admin Only)

List all users with pagination and filtering.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 50, max: 100)
- `username`: Filter by username (partial match)
- `email`: Filter by email (partial match)
- `is_active`: Filter by active status (true/false)
- `is_superuser`: Filter by superuser status (true/false)

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "johndoe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2025-01-20T10:30:00Z",
      "updated_at": "2025-01-20T10:30:00Z"
    }
  ],
  "total_count": 1
}
```

## Conversations

### POST /api/v1/conversations

Create a new conversation.

**Request Body:**
```json
{
  "title": "AI Discussion",
  "is_active": true,
  "metainfo": {
    "category": "technical",
    "priority": "normal"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "AI Discussion",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_active": true,
    "metainfo": {
      "category": "technical",
      "priority": "normal"
    },
    "message_count": 0,
    "created_at": "2025-01-20T10:30:00Z",
    "updated_at": "2025-01-20T10:30:00Z",
    "last_message_at": null
  }
}
```

### GET /api/v1/conversations

List user conversations with pagination.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 50)
- `is_active`: Filter by active status

**Response:**
```json
{
  "success": true,
  "conversations": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "title": "AI Discussion",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "is_active": true,
      "message_count": 5,
      "created_at": "2025-01-20T10:30:00Z",
      "updated_at": "2025-01-20T10:30:00Z",
      "last_message_at": "2025-01-20T11:45:00Z"
    }
  ],
  "total_count": 1
}
```

### POST /api/v1/conversations/{conversation_id}/messages

Send a message in a conversation.

**Request Body:**
```json
{
  "content": "What are the benefits of machine learning?",
  "role": "user",
  "metadata": {
    "source": "web_ui"
  },
  "tool_handling_mode": "auto"
}
```

**Response:**
```json
{
  "success": true,
  "conversation": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "AI Discussion",
    "message_count": 2
  },
  "user_message": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "conversation_id": "660e8400-e29b-41d4-a716-446655440000",
    "role": "user",
    "content": "What are the benefits of machine learning?",
    "metadata": {
      "source": "web_ui"
    },
    "created_at": "2025-01-20T10:30:00Z"
  },
  "assistant_message": {
    "id": "880e8400-e29b-41d4-a716-446655440000",
    "conversation_id": "660e8400-e29b-41d4-a716-446655440000",
    "role": "assistant",
    "content": "Machine learning offers numerous benefits including...",
    "tool_calls": [],
    "created_at": "2025-01-20T10:30:15Z"
  }
}
```

### GET /api/v1/conversations/{conversation_id}/messages

Get messages from a conversation.

**Query Parameters:**
- `skip`: Number of messages to skip (default: 0)
- `limit`: Maximum messages to return (default: 50)

**Response:**
```json
{
  "success": true,
  "messages": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "conversation_id": "660e8400-e29b-41d4-a716-446655440000",
      "role": "user",
      "content": "What are the benefits of machine learning?",
      "metadata": {
        "source": "web_ui"
      },
      "created_at": "2025-01-20T10:30:00Z"
    }
  ],
  "total_count": 1
}
```

## Documents

### POST /api/v1/documents/upload

Upload and process a document.

**Request:**
```
Content-Type: multipart/form-data

file: <binary file data>
title: "Research Paper" (optional)
metadata: {"category": "research"} (optional JSON)
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "990e8400-e29b-41d4-a716-446655440000",
    "title": "Research Paper",
    "filename": "research.pdf",
    "file_type": "pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "processing_status": "processing",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "metainfo": {
      "category": "research"
    },
    "chunk_count": 0,
    "created_at": "2025-01-20T10:30:00Z",
    "updated_at": "2025-01-20T10:30:00Z"
  }
}
```

### GET /api/v1/documents

List user documents.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 50)
- `file_type`: Filter by file type
- `processing_status`: Filter by processing status

**Response:**
```json
{
  "success": true,
  "documents": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "title": "Research Paper",
      "filename": "research.pdf",
      "file_type": "pdf",
      "file_size": 2048576,
      "processing_status": "completed",
      "chunk_count": 25,
      "created_at": "2025-01-20T10:30:00Z"
    }
  ],
  "total_count": 1
}
```

### GET /api/v1/documents/{document_id}

Get document details.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "990e8400-e29b-41d4-a716-446655440000",
    "title": "Research Paper",
    "filename": "research.pdf",
    "file_type": "pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "processing_status": "completed",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "metainfo": {
      "category": "research",
      "pages": 50,
      "language": "en"
    },
    "chunk_count": 25,
    "created_at": "2025-01-20T10:30:00Z",
    "updated_at": "2025-01-20T10:35:00Z"
  }
}
```

### DELETE /api/v1/documents/{document_id}

Delete a document.

**Response:**
```json
{
  "success": true,
  "message": "Document deleted successfully"
}
```

## Search

### GET /api/v1/search/documents

Search through document content using RAG.

**Query Parameters:**
- `query`: Search query (required)
- `limit`: Maximum results to return (default: 10)
- `min_score`: Minimum relevance score (default: 0.5)

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "document": {
        "id": "990e8400-e29b-41d4-a716-446655440000",
        "title": "Research Paper",
        "filename": "research.pdf"
      },
      "chunks": [
        {
          "id": "aa0e8400-e29b-41d4-a716-446655440000",
          "content": "Machine learning is a subset of artificial intelligence...",
          "chunk_index": 5,
          "metadata": {
            "page": 3,
            "section": "Introduction"
          }
        }
      ],
      "relevance_score": 0.85
    }
  ],
  "total_count": 1
}
```

## Health

### GET /api/v1/health

Get API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-20T10:30:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "storage": "healthy"
  }
}
```

## Error Handling

All API endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid input data",
  "details": {
    "field": "username",
    "error": "Username must be at least 3 characters"
  },
  "timestamp": "2025-01-20T10:30:00Z"
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "error_code": "UNAUTHORIZED",
  "message": "Authentication required",
  "timestamp": "2025-01-20T10:30:00Z"
}
```

### 403 Forbidden
```json
{
  "success": false,
  "error_code": "FORBIDDEN",
  "message": "Insufficient privileges",
  "timestamp": "2025-01-20T10:30:00Z"
}
```

### 404 Not Found
```json
{
  "success": false,
  "error_code": "NOT_FOUND",
  "message": "Resource not found",
  "timestamp": "2025-01-20T10:30:00Z"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error_code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred",
  "timestamp": "2025-01-20T10:30:00Z"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Standard endpoints**: 100 requests per minute per IP
- **Authentication endpoints**: 10 requests per minute per IP
- **Upload endpoints**: 5 requests per minute per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642681800
```

When rate limit is exceeded:
```json
{
  "success": false,
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests, please try again later",
  "timestamp": "2025-01-20T10:30:00Z"
}
```