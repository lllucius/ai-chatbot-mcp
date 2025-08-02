"""
Comprehensive database models package for enterprise data management and persistence.

This package provides the complete data model architecture for the AI Chatbot Platform,
implementing sophisticated database models with advanced ORM patterns, comprehensive
relationships, and enterprise-grade data integrity enforcement. All models follow
industry-standard design patterns with proper separation of concerns, extensive
validation, and optimal performance characteristics for high-throughput production
environments with comprehensive audit trails and data governance capabilities.

Key Features:
- SQLAlchemy ORM models with advanced relationship mapping and lazy loading optimization
- UUID-based primary keys ensuring global uniqueness and distributed system compatibility
- Comprehensive timestamp tracking with creation and modification audit trails
- Advanced validation and constraint enforcement with business rule implementation
- Optimized database schema design with proper indexing and query performance
- Enterprise-grade data integrity with foreign key constraints and cascade management

Database Architecture:
- Base model classes providing common functionality and consistent patterns across all entities
- Mixin classes for timestamp tracking, UUID generation, and audit trail capabilities
- Comprehensive relationship modeling with proper foreign key constraints and referential integrity
- Advanced indexing strategies for optimal query performance and data retrieval efficiency
- Database migration support with version control and rollback capabilities
- Connection pooling and transaction management for high-concurrency environments

Core Models:
- **User Management**: Complete user lifecycle with authentication, profiles, and security controls
- **Document Processing**: Advanced document storage with chunking, embedding, and metadata management
- **Conversation Handling**: Sophisticated chat conversation tracking with message history and threading
- **MCP Integration**: Model Context Protocol server and tool registration with configuration management
- **LLM Profiles**: Large Language Model configuration and prompt template management
- **Audit and Security**: Comprehensive logging, monitoring, and compliance tracking capabilities

Data Integrity Features:
- Comprehensive validation at model level preventing invalid data persistence
- Foreign key constraints ensuring referential integrity across all relationships
- Business rule enforcement through model methods and property validation
- Automatic timestamp management with creation and modification tracking
- Soft delete capabilities preserving data for audit and recovery purposes
- Version control and change tracking for critical business entities

Performance Optimization:
- Lazy loading relationships preventing N+1 query problems and unnecessary data fetching
- Strategic indexing on frequently queried columns and foreign key relationships
- Query optimization through proper join strategies and relationship configuration
- Connection pooling and transaction batching for high-throughput scenarios
- Caching integration with Redis for frequently accessed data and session management
- Database query profiling and optimization recommendations for continuous improvement

Security and Compliance:
- Data encryption at rest and in transit with industry-standard cryptographic algorithms
- Access control integration with role-based permissions and audit logging
- PII data handling with proper anonymization and retention policies
- GDPR compliance with data portability and right-to-be-forgotten capabilities
- Comprehensive audit trails for regulatory compliance and forensic analysis
- Data classification and handling according to enterprise security policies

Enterprise Integration:
- Multi-tenant architecture support with data isolation and tenant-specific configurations
- Database replication and high availability with automatic failover capabilities
- Backup and disaster recovery integration with point-in-time recovery
- Monitoring and alerting integration with database performance and health metrics
- ETL pipeline integration for data warehouse and analytics platform connectivity
- API integration for external system data synchronization and real-time updates

Model Categories:

**Foundation Models:**
- BaseModelDB: Core database model with common fields and functionality
- TimestampMixin: Timestamp tracking for creation and modification audit trails
- UUIDMixin: UUID primary key generation ensuring global uniqueness

**User Management Models:**
- User: Complete user entity with authentication, profiles, and security controls

**Content Management Models:**
- Document: Document storage and metadata with version control and access management
- DocumentChunk: Document segmentation for vector embeddings and efficient retrieval

**Conversation Models:**
- Conversation: Chat session management with threading and participant tracking
- Message: Individual message entities with content, metadata, and relationship management

**Integration Models:**
- MCPServer: Model Context Protocol server registration and configuration management
- MCPTool: MCP tool definitions with capabilities and integration specifications
- LLMProfile: Large Language Model configuration and prompt template management
- Prompt: Reusable prompt templates with versioning and performance tracking

Use Cases:
- Enterprise application data persistence with comprehensive business logic enforcement
- Multi-tenant SaaS platform data isolation and tenant-specific configuration management
- Audit and compliance tracking with detailed change history and regulatory reporting
- High-performance API backend with optimized data access patterns and caching strategies
- Integration hub for external system data synchronization and real-time processing
- Analytics and reporting foundation with comprehensive data lineage and quality assurance
"""

# Import SQLAlchemy base classes only
from .base import BaseModelDB, TimestampMixin, UUIDMixin
from .conversation import Conversation, Message
from .document import Document, DocumentChunk
from .llm_profile import LLMProfile

# Import new registry models
from .mcp_server import MCPServer
from .mcp_tool import MCPTool
from .prompt import Prompt

# Import database models (SQLAlchemy)
from .user import User

__all__ = [
    # Base classes
    "BaseModelDB",
    "TimestampMixin",
    "UUIDMixin",
    # Models
    "User",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
    # Registry models
    "MCPServer",
    "MCPTool",
    "Prompt",
    "LLMProfile",
]
