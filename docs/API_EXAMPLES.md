# Enhanced API Documentation with Examples

## Overview

The AI Chatbot Platform API has been enhanced with advanced document processing capabilities, background task management, and comprehensive configuration options. This document provides practical examples for all enhanced endpoints.

## Authentication

All API requests require authentication using JWT tokens.

```python
import httpx

# Login to get access token
response = httpx.post("http://localhost:8000/api/v1/auth/login", json={
    "username": "your_username", 
    "password": "your_password"
})

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
```

## Enhanced Document Upload

Upload documents with automatic background processing:

```python
# Upload document with auto-processing
with open("document.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "title": "Important Research Paper",
        "auto_process": True,
        "processing_priority": 3
    }
    
    response = httpx.post(
        "http://localhost:8000/api/v1/documents/upload",
        files=files,
        data=data,
        headers=headers,
        timeout=30.0
    )

result = response.json()
print(f"Document uploaded: {result['document']['id']}")
print(f"Processing task ID: {result['task_id']}")
```

## Processing Status Monitoring

Get comprehensive status including background task information:

```python
document_id = "550e8400-e29b-41d4-a716-446655440000"
task_id = "task-12345"

response = httpx.get(
    f"http://localhost:8000/api/v1/documents/{document_id}/enhanced-status",
    params={"task_id": task_id},
    headers=headers
)

status = response.json()
print(f"Document status: {status['status']}")
print(f"Task progress: {status['progress']*100:.1f}%")
print(f"Chunks created: {status['chunk_count']}")
```

## Configuration Management

Retrieve current processing parameters:

```python
response = httpx.get(
    "http://localhost:8000/api/v1/documents/processing-config",
    headers=headers
)

config = response.json()['config']
print(f"Default chunk size: {config['default_chunk_size']}")
print(f"Supported formats: {config['supported_formats']}")
```

## Background Processing Management

Monitor the background processing queue:

```python
response = httpx.get(
    "http://localhost:8000/api/v1/documents/queue-status", 
    headers=headers
)

queue_info = response.json()
print(f"Queue size: {queue_info['queue_size']}")
print(f"Active tasks: {queue_info['active_tasks']}")
```

This comprehensive API documentation provides practical examples for utilizing all the enhanced features of the AI Chatbot Platform.