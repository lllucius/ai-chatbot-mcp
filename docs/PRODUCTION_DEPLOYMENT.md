"""
Production Deployment Guide for AI Chatbot Platform

This guide provides comprehensive instructions for deploying the enhanced AI Chatbot Platform
to production environments with proper configuration, security, and monitoring.

Enhanced Features in Production:
- Advanced document processing with 20+ formats
- Background task processing with Redis/Celery
- Comprehensive monitoring and logging
- Performance optimization and caching
- Security hardening and best practices

Version: 2.0
"""

# Production Deployment Guide

## Overview

The AI Chatbot Platform now includes enhanced document processing capabilities, background task processing, and comprehensive monitoring. This guide covers production deployment with all enhanced features.

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Python**: 3.11 or 3.12
- **PostgreSQL**: 14+ with pgvector extension
- **Redis**: 6.0+ (for background processing)
- **Memory**: 8GB minimum, 16GB recommended
- **Storage**: 100GB minimum for documents and logs
- **CPU**: 4 cores minimum, 8 cores recommended

### Required Services

```bash
# Install PostgreSQL with pgvector
sudo apt update
sudo apt install postgresql postgresql-contrib postgresql-14-pgvector

# Install Redis
sudo apt install redis-server

# Install Python dependencies
sudo apt install python3.11 python3.11-venv python3.11-dev
sudo apt install build-essential libpq-dev

# Install system dependencies for document processing  
sudo apt install tesseract-ocr tesseract-ocr-eng
sudo apt install poppler-utils
sudo apt install libreoffice --headless
```

## Enhanced Configuration

### Environment Variables

Create `/etc/ai-chatbot/.env.production`:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://chatbot_user:secure_password@localhost:5432/ai_chatbot_prod

# Security Configuration
SECRET_KEY=your-256-bit-production-secret-key-here-must-be-very-long-and-secure
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# OpenAI Configuration
OPENAI_API_KEY=sk-your-production-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Application Configuration
APP_NAME=AI Chatbot Platform
APP_VERSION=2.0.0
DEBUG=false
LOG_LEVEL=INFO

# Enhanced Document Processing
DEFAULT_CHUNK_SIZE=1000
DEFAULT_CHUNK_OVERLAP=200
MAX_CHUNK_SIZE=4000
MIN_CHUNK_SIZE=100
MAX_CONCURRENT_PROCESSING=5
PROCESSING_TIMEOUT=3600

# Text Preprocessing
ENABLE_TEXT_PREPROCESSING=true
NORMALIZE_UNICODE=true
REMOVE_EXTRA_WHITESPACE=true
LANGUAGE_DETECTION=true

# Background Processing
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# File Upload Configuration
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_DIRECTORY=/var/lib/ai-chatbot/uploads
ALLOWED_FILE_TYPES=pdf,docx,doc,odt,rtf,txt,md,markdown,rst,html,htm,xhtml,csv,tsv,json,jsonl,xml,xlsx,xls,ods,pptx,ppt,odp,epub,eml,msg

# Performance and Caching
ENABLE_CACHING=true
CACHE_TTL=3600
MAX_CONNECTIONS=100

# Monitoring and Logging
LOG_FILE=/var/log/ai-chatbot/app.log
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30

# Security
CORS_ORIGINS=https://your-domain.com
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_PERIOD=3600
```

This comprehensive guide ensures a robust, secure, and scalable production deployment of the enhanced AI Chatbot Platform.
