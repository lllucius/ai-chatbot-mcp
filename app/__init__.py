"""AI Chatbot Platform - Enterprise-grade AI chatbot with advanced RAG capabilities.

This package provides a comprehensive, production-ready AI chatbot platform featuring
advanced document processing, semantic vector search, and intelligent conversation management.
Built with FastAPI, PostgreSQL with PGVector, and OpenAI integration for enterprise deployment.
"""

from app.main import app

__version__ = "1.0.0"
__description__ = "Production-grade AI chatbot platform with RAG capabilities"
__author__ = "lllucius"
__license__ = "MIT"


__all__ = ["app"]
