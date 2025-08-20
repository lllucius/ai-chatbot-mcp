# LangChain and LlamaIndex Migration Guide

This guide provides comprehensive instructions for converting the ai-chatbot-mcp repository from direct OpenAI API integration to using LangChain and LlamaIndex frameworks.

## Table of Contents

1. [Overview](#overview)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Target Architecture](#target-architecture)
4. [Migration Strategy](#migration-strategy)
5. [Phase 1: Core Dependencies](#phase-1-core-dependencies)
6. [Phase 2: LLM Client Migration](#phase-2-llm-client-migration)
7. [Phase 3: Embedding Service Migration](#phase-3-embedding-service-migration)
8. [Phase 4: Vector Store Integration](#phase-4-vector-store-integration)
9. [Phase 5: Document Processing](#phase-5-document-processing)
10. [Phase 6: Advanced RAG with LlamaIndex](#phase-6-advanced-rag-with-llamaindex)
11. [Phase 7: Conversation Chains](#phase-7-conversation-chains)
12. [Testing and Validation](#testing-and-validation)
13. [Backwards Compatibility](#backwards-compatibility)
14. [Performance Considerations](#performance-considerations)

## Overview

The current ai-chatbot-mcp system uses direct OpenAI API integration for LLM interactions and custom implementations for vector search and RAG. This migration will:

- Replace direct OpenAI API calls with LangChain abstractions
- Integrate LlamaIndex for advanced RAG capabilities
- Maintain existing FastMCP tool integration
- Preserve database schema and API contracts
- Improve modularity and extensibility

## Current Architecture Analysis

### Key Components to Migrate

| Component | Current Implementation | Migration Target |
|-----------|----------------------|------------------|
| `OpenAIClient` | Direct OpenAI API | LangChain ChatOpenAI |
| `EmbeddingService` | OpenAI Embeddings API | LangChain OpenAIEmbeddings |
| `SearchService` | Custom PGVector | LangChain VectorStore + LlamaIndex |
| `FileProcessor` | Unstructured library | LangChain DocumentLoaders |
| `ConversationService` | Custom chat logic | LangChain ConversationChain |
| Profile Management | Custom parameter handling | LangChain model configuration |

### Current Dependencies
```
openai==1.99.6
unstructured==0.18.9
pgvector==0.2.4
tiktoken==0.9.0
```

## Target Architecture

### New Framework Integration
- **LangChain**: Core LLM abstractions, chains, and agents
- **LlamaIndex**: Advanced RAG, document indexing, and query engines
- **LangSmith**: Observability and debugging (optional)
- **LangServe**: API deployment utilities (optional)

### Hybrid Approach Benefits
1. **LangChain** for LLM interactions and basic chains
2. **LlamaIndex** for sophisticated RAG and document understanding
3. **Maintained MCP integration** for tool calling
4. **Preserved FastAPI** structure for API endpoints

## Migration Strategy

### Incremental Migration Approach
1. **Parallel Implementation**: Keep existing code while building new LangChain/LlamaIndex versions
2. **Feature Flags**: Use configuration to switch between old and new implementations
3. **Gradual Rollout**: Migrate components one at a time
4. **Comprehensive Testing**: Validate functionality at each step

### Risk Mitigation
- Maintain API compatibility
- Preserve database schema
- Keep MCP tool integration intact
- Ensure performance parity

## Phase 1: Core Dependencies

### Update requirements.txt
```bash
# Add new dependencies while keeping existing ones
langchain==0.2.11
langchain-openai==0.1.17
langchain-core==0.2.23
langchain-community==0.2.10
llamaindex==0.10.43
llama-index-core==0.10.43
llama-index-embeddings-openai==0.1.9
llama-index-llms-openai==0.1.22
llama-index-vector-stores-postgres==0.1.4
```

### Configuration Updates
```python
# app/config.py - Add new configuration options
class Settings(BaseSettings):
    # Existing settings...
    
    # LangChain settings
    langchain_verbose: bool = False
    langchain_debug: bool = False
    langsmith_api_key: Optional[str] = None
    langsmith_project: Optional[str] = None
    
    # LlamaIndex settings
    llamaindex_cache_dir: str = "cache/llamaindex"
    llamaindex_chunk_size: int = 1024
    llamaindex_chunk_overlap: int = 200
    
    # Migration settings
    use_langchain: bool = False  # Feature flag
    use_llamaindex: bool = False  # Feature flag
```

## Phase 2: LLM Client Migration

### Create LangChain-based LLM Service

```python
# app/services/langchain_llm.py
from typing import Any, Dict, List, Optional, Union
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
from app.config import settings
from app.models.profile import LLMProfile

class LangChainLLMService:
    """LangChain-based LLM service replacing OpenAIClient."""
    
    def __init__(self):
        self.default_llm = ChatOpenAI(
            model=settings.openai_chat_model,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            temperature=0.7,
            verbose=settings.langchain_verbose
        )
        self.llm_cache = {}
    
    def _get_llm_from_profile(self, llm_profile: Optional[LLMProfile] = None) -> ChatOpenAI:
        """Create LLM instance from profile parameters."""
        if not llm_profile:
            return self.default_llm
        
        profile_key = f"{llm_profile.model_name}_{llm_profile.id}"
        if profile_key not in self.llm_cache:
            params = llm_profile.to_openai_params()
            self.llm_cache[profile_key] = ChatOpenAI(
                model=llm_profile.model_name,
                openai_api_key=settings.openai_api_key,
                openai_api_base=settings.openai_base_url,
                **params
            )
        return self.llm_cache[profile_key]
    
    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[BaseMessage]:
        """Convert dict messages to LangChain message objects."""
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:  # user or other
                langchain_messages.append(HumanMessage(content=content))
        
        return langchain_messages
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        llm_profile: Optional[LLMProfile] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """LangChain-based chat completion."""
        llm = self._get_llm_from_profile(llm_profile)
        langchain_messages = self._convert_messages(messages)
        
        try:
            response = await llm.ainvoke(langchain_messages)
            
            # Convert back to expected format
            return {
                "content": response.content,
                "role": "assistant",
                "finish_reason": "stop",
                "usage": {
                    "prompt_tokens": llm.get_num_tokens_from_messages(langchain_messages),
                    "completion_tokens": llm.get_num_tokens(response.content),
                    "total_tokens": llm.get_num_tokens_from_messages(langchain_messages) + llm.get_num_tokens(response.content)
                }
            }
        except Exception as e:
            raise Exception(f"LangChain chat completion failed: {e}")
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        llm_profile: Optional[LLMProfile] = None,
        **kwargs
    ):
        """LangChain-based streaming chat completion."""
        llm = self._get_llm_from_profile(llm_profile)
        langchain_messages = self._convert_messages(messages)
        
        async for chunk in llm.astream(langchain_messages):
            yield {
                "type": "content",
                "content": chunk.content
            }
```

### Update OpenAI Client with Feature Flag

```python
# app/services/openai_client.py - Add migration support
class OpenAIClient:
    def __init__(self, mcp_service: Optional[MCPService] = None):
        self.mcp_service = mcp_service
        # Keep existing initialization...
        
        # Add LangChain integration
        if settings.use_langchain:
            from app.services.langchain_llm import LangChainLLMService
            self.langchain_service = LangChainLLMService()
        else:
            self.langchain_service = None
    
    async def chat_completion(self, *args, **kwargs) -> Dict[str, Any]:
        """Route to LangChain or original implementation based on feature flag."""
        if settings.use_langchain and self.langchain_service:
            return await self.langchain_service.chat_completion(*args, **kwargs)
        else:
            # Keep existing implementation as fallback
            return await self._original_chat_completion(*args, **kwargs)
    
    async def _original_chat_completion(self, *args, **kwargs):
        """Renamed original implementation for backwards compatibility."""
        # Move existing chat_completion logic here
        pass
```

## Phase 3: Embedding Service Migration

### Create LangChain Embedding Service

```python
# app/services/langchain_embedding.py
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from app.config import settings

class LangChainEmbeddingService:
    """LangChain-based embedding service."""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url
        )
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using LangChain."""
        if not text or not text.strip():
            return None
        
        try:
            embedding = await self.embeddings.aembed_query(text.strip())
            return embedding
        except Exception as e:
            logger.error(f"LangChain embedding generation failed: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        if not valid_texts:
            return [None] * len(texts)
        
        try:
            embeddings = await self.embeddings.aembed_documents(valid_texts)
            result = []
            valid_idx = 0
            
            for text in texts:
                if text and text.strip():
                    result.append(embeddings[valid_idx])
                    valid_idx += 1
                else:
                    result.append(None)
            
            return result
        except Exception as e:
            logger.error(f"LangChain batch embedding generation failed: {e}")
            return [None] * len(texts)
```

### Update Existing Embedding Service

```python
# app/services/embedding.py - Add LangChain integration
class EmbeddingService:
    def __init__(self, db: AsyncSession, **kwargs):
        # Keep existing initialization...
        
        # Add LangChain integration
        if settings.use_langchain:
            from app.services.langchain_embedding import LangChainEmbeddingService
            self.langchain_service = LangChainEmbeddingService()
        else:
            self.langchain_service = None
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Route to LangChain or original implementation."""
        if settings.use_langchain and self.langchain_service:
            return await self.langchain_service.generate_embedding(text)
        else:
            # Keep existing implementation
            return await self._original_generate_embedding(text)
```

## Phase 4: Vector Store Integration

### LangChain Vector Store Implementation

```python
# app/services/langchain_vectorstore.py
from typing import List, Optional, Tuple
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from app.config import settings
from app.services.langchain_embedding import LangChainEmbeddingService

class LangChainVectorStore:
    """LangChain-based vector store using PGVector."""
    
    def __init__(self):
        self.embeddings = LangChainEmbeddingService()
        
        # PGVector connection string
        connection_string = PGVector.connection_string_from_db_params(
            driver="psycopg2",
            host=settings.database_host,
            port=settings.database_port,
            database=settings.database_name,
            user=settings.database_user,
            password=settings.database_password,
        )
        
        self.vectorstore = PGVector(
            collection_name="document_chunks",
            connection_string=connection_string,
            embedding_function=self.embeddings.embeddings,
        )
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 10,
        filter: Optional[dict] = None
    ) -> List[Document]:
        """Perform similarity search using LangChain."""
        return await self.vectorstore.asimilarity_search(
            query=query,
            k=k,
            filter=filter
        )
    
    async def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 10,
        filter: Optional[dict] = None
    ) -> List[Tuple[Document, float]]:
        """Perform similarity search with scores."""
        return await self.vectorstore.asimilarity_search_with_score(
            query=query,
            k=k,
            filter=filter
        )
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to vector store."""
        return await self.vectorstore.aadd_documents(documents)
```

## Phase 5: Document Processing

### LangChain Document Loaders

```python
# app/services/langchain_document.py
from typing import List, Dict, Any
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import settings

class LangChainDocumentProcessor:
    """LangChain-based document processing."""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.llamaindex_chunk_size,
            chunk_overlap=settings.llamaindex_chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.loader_mapping = {
            "pdf": PyPDFLoader,
            "docx": Docx2txtLoader,
            "txt": TextLoader,
            "html": UnstructuredHTMLLoader,
            "md": UnstructuredMarkdownLoader,
        }
    
    async def extract_chunks(
        self, 
        file_path: str, 
        file_type: str, 
        max_characters: int = 1000
    ) -> List[Dict[str, Any]]:
        """Extract chunks using LangChain loaders and splitters."""
        file_type = file_type.lower().lstrip(".")
        
        if file_type not in self.loader_mapping:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Load document
        loader_class = self.loader_mapping[file_type]
        loader = loader_class(file_path)
        documents = await loader.aload()
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Convert to expected format
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "text": chunk.page_content,
                "chunk_index": i,
                "character_count": len(chunk.page_content),
                "metadata": chunk.metadata,
            })
        
        return result
```

## Phase 6: Advanced RAG with LlamaIndex

### LlamaIndex Service Implementation

```python
# app/services/llamaindex_service.py
from typing import List, Dict, Any, Optional
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from app.config import settings

class LlamaIndexService:
    """Advanced RAG using LlamaIndex."""
    
    def __init__(self):
        # Configure LlamaIndex settings
        Settings.llm = OpenAI(
            model=settings.openai_chat_model,
            api_key=settings.openai_api_key,
            api_base=settings.openai_base_url
        )
        
        Settings.embed_model = OpenAIEmbedding(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
            api_base=settings.openai_base_url
        )
        
        # Vector store configuration
        self.vector_store = PGVectorStore.from_params(
            database=settings.database_name,
            host=settings.database_host,
            password=settings.database_password,
            port=settings.database_port,
            user=settings.database_user,
            table_name="llamaindex_embeddings",
            embed_dim=1536  # OpenAI embedding dimension
        )
        
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store
        )
    
    async def create_query_engine(
        self,
        similarity_top_k: int = 10,
        similarity_cutoff: float = 0.7
    ):
        """Create a query engine with post-processing."""
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=similarity_top_k
        )
        
        postprocessor = SimilarityPostprocessor(
            similarity_cutoff=similarity_cutoff
        )
        
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            node_postprocessors=[postprocessor]
        )
        
        return query_engine
    
    async def query(
        self, 
        query_text: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Perform RAG query using LlamaIndex."""
        query_engine = await self.create_query_engine(**kwargs)
        
        response = await query_engine.aquery(query_text)
        
        return {
            "response": str(response),
            "source_nodes": [
                {
                    "content": node.node.text,
                    "score": node.score,
                    "metadata": node.node.metadata
                }
                for node in response.source_nodes
            ]
        }
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to LlamaIndex."""
        llamaindex_docs = [
            Document(
                text=doc["content"],
                metadata=doc.get("metadata", {})
            )
            for doc in documents
        ]
        
        self.index.insert_nodes(llamaindex_docs)
```

### RAG Service Integration

```python
# app/services/rag_service.py - New comprehensive RAG service
from typing import List, Dict, Any, Optional
from app.services.llamaindex_service import LlamaIndexService
from app.services.langchain_vectorstore import LangChainVectorStore
from app.config import settings

class RAGService:
    """Unified RAG service supporting both LangChain and LlamaIndex."""
    
    def __init__(self):
        if settings.use_llamaindex:
            self.llamaindex_service = LlamaIndexService()
        else:
            self.llamaindex_service = None
        
        if settings.use_langchain:
            self.langchain_vectorstore = LangChainVectorStore()
        else:
            self.langchain_vectorstore = None
    
    async def get_rag_context(
        self, 
        query: str, 
        user_id: int, 
        limit: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """Get RAG context using the configured service."""
        if settings.use_llamaindex and self.llamaindex_service:
            return await self._get_llamaindex_context(query, user_id, limit)
        elif settings.use_langchain and self.langchain_vectorstore:
            return await self._get_langchain_context(query, user_id, limit)
        else:
            # Fallback to existing search service
            return await self._get_legacy_context(query, user_id, limit)
    
    async def _get_llamaindex_context(
        self, query: str, user_id: int, limit: int
    ) -> List[Dict[str, Any]]:
        """Get context using LlamaIndex."""
        result = await self.llamaindex_service.query(
            query, 
            similarity_top_k=limit
        )
        
        return [
            {
                "content": node["content"],
                "similarity_score": node["score"],
                "metadata": node["metadata"]
            }
            for node in result["source_nodes"]
        ]
    
    async def _get_langchain_context(
        self, query: str, user_id: int, limit: int
    ) -> List[Dict[str, Any]]:
        """Get context using LangChain vector store."""
        results = await self.langchain_vectorstore.similarity_search_with_score(
            query=query,
            k=limit,
            filter={"user_id": user_id}
        )
        
        return [
            {
                "content": doc.page_content,
                "similarity_score": score,
                "metadata": doc.metadata
            }
            for doc, score in results
        ]
```

## Phase 7: Conversation Chains

### LangChain Conversation Chain Integration

```python
# app/services/langchain_conversation.py
from typing import List, Dict, Any, Optional
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from app.services.langchain_llm import LangChainLLMService
from app.services.rag_service import RAGService

class LangChainConversationService:
    """LangChain-based conversation management."""
    
    def __init__(self):
        self.llm_service = LangChainLLMService()
        self.rag_service = RAGService()
        self.conversations = {}  # In-memory conversation storage
    
    def _get_conversation_chain(
        self, 
        conversation_id: int, 
        llm_profile=None
    ) -> ConversationChain:
        """Get or create conversation chain for a conversation."""
        if conversation_id not in self.conversations:
            llm = self.llm_service._get_llm_from_profile(llm_profile)
            
            memory = ConversationBufferWindowMemory(
                k=10,  # Keep last 10 exchanges
                return_messages=True
            )
            
            prompt = PromptTemplate(
                input_variables=["history", "input"],
                template="""The following is a friendly conversation between a human and an AI assistant. The AI is helpful, creative, clever, and very friendly.

{history}
Human: {input}
AI Assistant:"""
            )
            
            self.conversations[conversation_id] = ConversationChain(
                llm=llm,
                memory=memory,
                prompt=prompt,
                verbose=settings.langchain_verbose
            )
        
        return self.conversations[conversation_id]
    
    async def process_message(
        self,
        conversation_id: int,
        message: str,
        use_rag: bool = False,
        llm_profile=None
    ) -> Dict[str, Any]:
        """Process a message using LangChain conversation chain."""
        chain = self._get_conversation_chain(conversation_id, llm_profile)
        
        # Add RAG context if enabled
        if use_rag:
            rag_context = await self.rag_service.get_rag_context(
                message, 
                user_id=conversation_id,  # Using conversation_id as proxy
                limit=5
            )
            
            if rag_context:
                context_text = "\n".join([
                    f"Context: {ctx['content']}" 
                    for ctx in rag_context
                ])
                message = f"Context information:\n{context_text}\n\nQuestion: {message}"
        
        response = await chain.ainvoke({"input": message})
        
        return {
            "content": response["response"],
            "rag_context": rag_context if use_rag else None
        }
```

## Testing and Validation

### Unit Tests for Migration Components

```python
# tests/test_migration.py
import pytest
from app.services.langchain_llm import LangChainLLMService
from app.services.langchain_embedding import LangChainEmbeddingService
from app.config import settings

@pytest.mark.asyncio
async def test_langchain_llm_service():
    """Test LangChain LLM service functionality."""
    service = LangChainLLMService()
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    response = await service.chat_completion(messages)
    
    assert "content" in response
    assert response["role"] == "assistant"
    assert "usage" in response

@pytest.mark.asyncio
async def test_langchain_embedding_service():
    """Test LangChain embedding service."""
    service = LangChainEmbeddingService()
    
    embedding = await service.generate_embedding("Test text")
    
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) > 0

@pytest.mark.asyncio
async def test_feature_flag_routing():
    """Test feature flag routing between old and new implementations."""
    settings.use_langchain = True
    
    # Test that LangChain implementation is used
    from app.services.openai_client import OpenAIClient
    client = OpenAIClient()
    
    assert client.langchain_service is not None
```

### Integration Tests

```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_end_to_end_conversation():
    """Test end-to-end conversation with LangChain."""
    settings.use_langchain = True
    settings.use_llamaindex = True
    
    # Create conversation service
    from app.services.langchain_conversation import LangChainConversationService
    service = LangChainConversationService()
    
    # Test message processing
    response = await service.process_message(
        conversation_id=1,
        message="What is artificial intelligence?",
        use_rag=True
    )
    
    assert "content" in response
    assert response["content"] is not None
```

### Performance Benchmarks

```python
# tests/test_performance.py
import time
import asyncio

async def benchmark_llm_services():
    """Benchmark old vs new LLM services."""
    # Benchmark original implementation
    start_time = time.time()
    # ... test original OpenAI client
    original_time = time.time() - start_time
    
    # Benchmark LangChain implementation
    start_time = time.time()
    # ... test LangChain service
    langchain_time = time.time() - start_time
    
    print(f"Original: {original_time:.2f}s, LangChain: {langchain_time:.2f}s")
```

## Backwards Compatibility

### Configuration Management

```python
# app/config.py - Extended configuration
class Settings(BaseSettings):
    # Migration feature flags
    use_langchain: bool = False
    use_llamaindex: bool = False
    migration_mode: str = "hybrid"  # "legacy", "hybrid", "new"
    
    # Backwards compatibility
    enable_legacy_api: bool = True
    api_version: str = "v1"  # Support for versioned APIs
```

### API Versioning

```python
# app/api/v1/ - Legacy API endpoints
# app/api/v2/ - New LangChain-powered endpoints

from fastapi import APIRouter
from app.config import settings

# V1 router (legacy)
v1_router = APIRouter(prefix="/v1")

# V2 router (LangChain/LlamaIndex)
v2_router = APIRouter(prefix="/v2")

@v1_router.post("/chat")
async def chat_v1(request: ChatRequest):
    """Legacy chat endpoint."""
    # Use original OpenAI client
    pass

@v2_router.post("/chat")
async def chat_v2(request: ChatRequest):
    """New LangChain-powered chat endpoint."""
    # Use LangChain services
    pass
```

## Performance Considerations

### Optimization Strategies

1. **Connection Pooling**: Reuse LangChain/LlamaIndex connections
2. **Caching**: Implement caching for embeddings and responses
3. **Batch Processing**: Use batch operations where possible
4. **Memory Management**: Monitor memory usage with LlamaIndex
5. **Database Optimization**: Optimize vector store queries

### Monitoring and Observability

```python
# app/middleware/langchain_monitoring.py
from langchain.callbacks import BaseCallbackHandler
import logging

class LangChainMonitoringHandler(BaseCallbackHandler):
    """Custom callback handler for monitoring LangChain operations."""
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        logging.info(f"LLM started with {len(prompts)} prompts")
    
    def on_llm_end(self, response, **kwargs):
        logging.info(f"LLM completed: {response}")
    
    def on_llm_error(self, error, **kwargs):
        logging.error(f"LLM error: {error}")
```

## Implementation Roadmap

### Timeline and Milestones

| Phase | Duration | Tasks | Success Criteria |
|-------|----------|-------|------------------|
| Phase 1 | 1 week | Dependencies, Configuration | All packages installed, feature flags working |
| Phase 2 | 2 weeks | LLM Client Migration | LangChain LLM working with feature flag |
| Phase 3 | 1 week | Embedding Service | LangChain embeddings generating correctly |
| Phase 4 | 2 weeks | Vector Store Integration | Vector search working with LangChain |
| Phase 5 | 1 week | Document Processing | LangChain loaders processing documents |
| Phase 6 | 3 weeks | LlamaIndex RAG | Advanced RAG features working |
| Phase 7 | 2 weeks | Conversation Chains | Full conversation flow with LangChain |
| Testing | 2 weeks | Comprehensive Testing | All tests passing, performance validated |

### Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance Degradation | High | Benchmark and optimize at each phase |
| API Breaking Changes | Medium | Maintain backwards compatibility |
| Database Schema Changes | Low | Use existing schema with new tables |
| Tool Integration Issues | Medium | Preserve MCP integration |

## Conclusion

This migration guide provides a comprehensive roadmap for converting the ai-chatbot-mcp repository to use LangChain and LlamaIndex. The incremental approach ensures minimal disruption while enabling advanced RAG capabilities and improved modularity.

Key benefits of the migration:
- **Improved Abstractions**: LangChain provides better LLM abstractions
- **Advanced RAG**: LlamaIndex offers sophisticated document understanding
- **Better Extensibility**: Easier to add new features and integrations
- **Community Support**: Access to larger ecosystem and community
- **Future-Proofing**: Better positioned for new developments in the space

The feature flag approach allows for gradual rollout and easy rollback if issues arise, ensuring a smooth transition from the current implementation to the new LangChain/LlamaIndex-powered system.