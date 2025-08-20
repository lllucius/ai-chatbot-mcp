# Implementation Examples and Code Samples

This document provides detailed implementation examples for migrating specific components from direct OpenAI integration to LangChain and LlamaIndex.

## Table of Contents

1. [Service Layer Examples](#service-layer-examples)
2. [API Endpoint Modifications](#api-endpoint-modifications)
3. [Database Integration](#database-integration)
4. [Configuration Examples](#configuration-examples)
5. [Testing Examples](#testing-examples)
6. [Migration Scripts](#migration-scripts)

## Service Layer Examples

### Complete LangChain LLM Service Implementation

```python
# app/services/langchain_llm_service.py
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tools import BaseTool, StructuredTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferWindowMemory
import asyncio
import json
import logging

from app.config import settings
from app.models.profile import LLMProfile
from app.services.mcp_service import MCPService
from shared.schemas.tool_calling import ToolHandlingMode

logger = logging.getLogger(__name__)

class TokenCountingHandler(BaseCallbackHandler):
    """Callback handler to track token usage."""
    
    def __init__(self):
        self.token_count = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        # Estimate prompt tokens (rough approximation)
        for prompt in prompts:
            self.token_count["prompt_tokens"] += len(str(prompt).split()) * 1.3
    
    def on_llm_end(self, response, **kwargs):
        # Estimate completion tokens
        if hasattr(response, 'generations'):
            for generation in response.generations:
                for gen in generation:
                    self.token_count["completion_tokens"] += len(str(gen.text).split()) * 1.3
        
        self.token_count["total_tokens"] = self.token_count["prompt_tokens"] + self.token_count["completion_tokens"]

class LangChainLLMService:
    """Enhanced LangChain-based LLM service with tool integration."""
    
    def __init__(self, mcp_service: Optional[MCPService] = None):
        self.mcp_service = mcp_service
        self.default_llm = ChatOpenAI(
            model=settings.openai_chat_model,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            temperature=0.7,
            verbose=settings.langchain_verbose,
            streaming=True
        )
        self.llm_cache = {}
        self.tools_cache = {}
    
    def _get_llm_from_profile(self, llm_profile: Optional[LLMProfile] = None) -> ChatOpenAI:
        """Create LLM instance from profile parameters with caching."""
        if not llm_profile:
            return self.default_llm
        
        profile_key = f"{llm_profile.model_name}_{llm_profile.id}"
        if profile_key not in self.llm_cache:
            params = llm_profile.to_openai_params()
            self.llm_cache[profile_key] = ChatOpenAI(
                model=llm_profile.model_name,
                openai_api_key=settings.openai_api_key,
                openai_api_base=settings.openai_base_url,
                streaming=True,
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
                # Handle tool calls in assistant messages
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    # Create assistant message with tool calls
                    ai_msg = AIMessage(content=content or "")
                    ai_msg.tool_calls = tool_calls
                    langchain_messages.append(ai_msg)
                else:
                    langchain_messages.append(AIMessage(content=content))
            elif role == "tool":
                # Tool response message
                tool_call_id = msg.get("tool_call_id")
                langchain_messages.append(ToolMessage(
                    content=content,
                    tool_call_id=tool_call_id
                ))
            else:  # user or other
                langchain_messages.append(HumanMessage(content=content))
        
        return langchain_messages
    
    async def _get_langchain_tools(self) -> List[BaseTool]:
        """Convert MCP tools to LangChain tools."""
        if not self.mcp_service:
            return []
        
        if "langchain_tools" in self.tools_cache:
            return self.tools_cache["langchain_tools"]
        
        try:
            mcp_tools = await self.mcp_service.get_openai_tools()
            langchain_tools = []
            
            for tool in mcp_tools:
                # Create LangChain tool from MCP tool definition
                tool_func = self._create_tool_function(tool)
                
                langchain_tool = StructuredTool.from_function(
                    func=tool_func,
                    name=tool["function"]["name"],
                    description=tool["function"]["description"],
                    args_schema=tool["function"].get("parameters", {})
                )
                langchain_tools.append(langchain_tool)
            
            self.tools_cache["langchain_tools"] = langchain_tools
            return langchain_tools
        
        except Exception as e:
            logger.error(f"Failed to convert MCP tools to LangChain tools: {e}")
            return []
    
    def _create_tool_function(self, tool_def: Dict[str, Any]):
        """Create a callable function for a tool definition."""
        tool_name = tool_def["function"]["name"]
        
        async def tool_function(**kwargs) -> str:
            """Execute MCP tool and return result."""
            try:
                tool_call = {
                    "id": f"call_{tool_name}",
                    "name": tool_name,
                    "arguments": kwargs
                }
                
                results = await self.mcp_service.execute_tool_calls([tool_call])
                if results and len(results) > 0:
                    result = results[0]
                    if result.get("success"):
                        return json.dumps(result.get("content", ""))
                    else:
                        return f"Error: {result.get('error', 'Unknown error')}"
                return "No result from tool execution"
            
            except Exception as e:
                return f"Tool execution failed: {str(e)}"
        
        return tool_function
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        llm_profile: Optional[LLMProfile] = None,
        use_tools: bool = True,
        tool_handling_mode: ToolHandlingMode = ToolHandlingMode.COMPLETE_WITH_RESULTS,
        **kwargs
    ) -> Dict[str, Any]:
        """LangChain-based chat completion with tool support."""
        llm = self._get_llm_from_profile(llm_profile)
        langchain_messages = self._convert_messages(messages)
        
        # Setup token counting
        token_handler = TokenCountingHandler()
        
        try:
            if use_tools and self.mcp_service:
                # Use agent for tool-enabled completion
                return await self._chat_completion_with_tools(
                    langchain_messages, llm, tool_handling_mode, token_handler
                )
            else:
                # Direct LLM completion without tools
                return await self._chat_completion_direct(
                    langchain_messages, llm, token_handler
                )
        
        except Exception as e:
            logger.error(f"LangChain chat completion failed: {e}")
            raise Exception(f"LangChain chat completion failed: {e}")
    
    async def _chat_completion_direct(
        self, 
        messages: List[BaseMessage], 
        llm: ChatOpenAI, 
        token_handler: TokenCountingHandler
    ) -> Dict[str, Any]:
        """Direct LLM completion without tools."""
        response = await llm.ainvoke(messages, callbacks=[token_handler])
        
        return {
            "content": response.content,
            "role": "assistant",
            "finish_reason": "stop",
            "usage": token_handler.token_count,
            "tool_calls_executed": [],
            "tool_handling_mode": None
        }
    
    async def _chat_completion_with_tools(
        self, 
        messages: List[BaseMessage], 
        llm: ChatOpenAI, 
        tool_handling_mode: ToolHandlingMode,
        token_handler: TokenCountingHandler
    ) -> Dict[str, Any]:
        """Chat completion with tool support using LangChain agents."""
        tools = await self._get_langchain_tools()
        
        if not tools:
            return await self._chat_completion_direct(messages, llm, token_handler)
        
        # Create agent with tools
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant with access to tools. Use them when appropriate to help answer questions."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=settings.langchain_verbose,
            callbacks=[token_handler]
        )
        
        # Prepare input for agent
        input_text = ""
        chat_history = []
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                input_text = msg.content
            else:
                chat_history.append(msg)
        
        # Execute agent
        result = await agent_executor.ainvoke({
            "input": input_text,
            "chat_history": chat_history
        })
        
        # Extract tool calls executed (simplified)
        tool_calls_executed = []
        if hasattr(result, 'intermediate_steps'):
            for step in result.intermediate_steps:
                tool_calls_executed.append({
                    "tool_call_id": "agent_call",
                    "success": True,
                    "content": str(step),
                    "execution_time_ms": 0
                })
        
        return {
            "content": result["output"],
            "role": "assistant",
            "finish_reason": "stop",
            "usage": token_handler.token_count,
            "tool_calls_executed": tool_calls_executed,
            "tool_handling_mode": tool_handling_mode
        }
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        llm_profile: Optional[LLMProfile] = None,
        use_tools: bool = True,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming chat completion with LangChain."""
        llm = self._get_llm_from_profile(llm_profile)
        langchain_messages = self._convert_messages(messages)
        
        try:
            if use_tools and self.mcp_service:
                # For streaming with tools, we need a different approach
                async for chunk in self._stream_with_tools(langchain_messages, llm):
                    yield chunk
            else:
                # Direct streaming without tools
                async for chunk in llm.astream(langchain_messages):
                    yield {
                        "type": "content",
                        "content": chunk.content,
                        "finish_reason": None
                    }
                
                yield {
                    "type": "content",
                    "content": "",
                    "finish_reason": "stop"
                }
        
        except Exception as e:
            logger.error(f"LangChain streaming failed: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    async def _stream_with_tools(
        self, 
        messages: List[BaseMessage], 
        llm: ChatOpenAI
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream completion with tool support."""
        tools = await self._get_langchain_tools()
        
        if not tools:
            async for chunk in llm.astream(messages):
                yield {
                    "type": "content",
                    "content": chunk.content,
                    "finish_reason": None
                }
            return
        
        # For simplicity, execute tools first, then stream response
        # In a production system, you might want more sophisticated streaming
        try:
            # First get the tool-augmented response
            full_response = await self._chat_completion_with_tools(
                messages, llm, ToolHandlingMode.COMPLETE_WITH_RESULTS, TokenCountingHandler()
            )
            
            # Stream the response content
            content = full_response.get("content", "")
            words = content.split()
            
            for i, word in enumerate(words):
                await asyncio.sleep(0.01)  # Simulate streaming delay
                yield {
                    "type": "content",
                    "content": word + (" " if i < len(words) - 1 else ""),
                    "finish_reason": None
                }
            
            # Yield tool calls if any
            tool_calls = full_response.get("tool_calls_executed", [])
            for tool_call in tool_calls:
                yield {
                    "type": "tool_call",
                    "tool": tool_call.get("tool_call_id", "unknown"),
                    "result": tool_call.get("content", "")
                }
            
            yield {
                "type": "content",
                "content": "",
                "finish_reason": "stop"
            }
        
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e)
            }
```

### LlamaIndex RAG Service with Advanced Features

```python
# app/services/llamaindex_rag_service.py
from typing import List, Dict, Any, Optional, Tuple
from llama_index.core import VectorStoreIndex, Document, Settings, StorageContext
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor, LLMRerank
from llama_index.core.node_parser import SimpleNodeParser, SentenceSplitter
from llama_index.core.extractors import TitleExtractor, QuestionsAnsweredExtractor
from llama_index.core.ingestion import IngestionPipeline
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
import logging
from datetime import datetime

from app.config import settings
from app.models.document import Document as DBDocument, DocumentChunk

logger = logging.getLogger(__name__)

class LlamaIndexRAGService:
    """Advanced RAG service using LlamaIndex with sophisticated features."""
    
    def __init__(self, db_session):
        self.db = db_session
        
        # Configure LlamaIndex settings
        Settings.llm = OpenAI(
            model=settings.openai_chat_model,
            api_key=settings.openai_api_key,
            api_base=settings.openai_base_url,
            temperature=0.1  # Lower temperature for factual responses
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
            table_name="llamaindex_vectors",
            embed_dim=1536,
            hnsw_kwargs={
                "hnsw_m": 16,
                "hnsw_ef_construction": 64,
                "hnsw_ef_search": 40
            }
        )
        
        # Storage context
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # Index
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context
        )
        
        # Node parser with custom settings
        self.node_parser = SentenceSplitter(
            chunk_size=settings.llamaindex_chunk_size,
            chunk_overlap=settings.llamaindex_chunk_overlap,
            separator=" ",
            paragraph_separator="\n\n"
        )
        
        # Ingestion pipeline
        self.ingestion_pipeline = IngestionPipeline(
            transformations=[
                self.node_parser,
                TitleExtractor(nodes=5),
                QuestionsAnsweredExtractor(questions=3),
                Settings.embed_model
            ]
        )
    
    async def create_advanced_query_engine(
        self,
        similarity_top_k: int = 20,
        similarity_cutoff: float = 0.7,
        use_reranking: bool = True,
        rerank_top_n: int = 5
    ):
        """Create an advanced query engine with multiple post-processors."""
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=similarity_top_k
        )
        
        postprocessors = [
            SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)
        ]
        
        # Add LLM reranking for better results
        if use_reranking:
            reranker = LLMRerank(
                llm=Settings.llm,
                top_n=rerank_top_n,
                choice_batch_size=10
            )
            postprocessors.append(reranker)
        
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            node_postprocessors=postprocessors,
            response_mode="compact"  # More concise responses
        )
        
        return query_engine
    
    async def query_with_context(
        self, 
        query_text: str,
        user_id: Optional[int] = None,
        document_ids: Optional[List[int]] = None,
        **engine_kwargs
    ) -> Dict[str, Any]:
        """Perform RAG query with user and document filtering."""
        
        # Create filtered query engine if needed
        if user_id or document_ids:
            filtered_index = await self._create_filtered_index(user_id, document_ids)
            if filtered_index:
                query_engine = await self._create_query_engine_from_index(
                    filtered_index, **engine_kwargs
                )
            else:
                query_engine = await self.create_advanced_query_engine(**engine_kwargs)
        else:
            query_engine = await self.create_advanced_query_engine(**engine_kwargs)
        
        try:
            # Execute query
            response = await query_engine.aquery(query_text)
            
            # Extract and format source information
            sources = []
            for node in response.source_nodes:
                source_info = {
                    "content": node.node.text,
                    "score": getattr(node, 'score', 0.0),
                    "metadata": node.node.metadata,
                    "node_id": node.node.node_id,
                    "document_id": node.node.metadata.get("document_id"),
                    "chunk_index": node.node.metadata.get("chunk_index")
                }
                sources.append(source_info)
            
            return {
                "response": str(response),
                "sources": sources,
                "query": query_text,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "num_sources": len(sources),
                    "avg_score": sum(s["score"] for s in sources) / len(sources) if sources else 0,
                    "engine_config": engine_kwargs
                }
            }
        
        except Exception as e:
            logger.error(f"LlamaIndex query failed: {e}")
            raise Exception(f"RAG query failed: {e}")
    
    async def _create_filtered_index(
        self, 
        user_id: Optional[int], 
        document_ids: Optional[List[int]]
    ) -> Optional[VectorStoreIndex]:
        """Create a filtered index based on user and document constraints."""
        try:
            # Build filter conditions for vector store
            filters = {}
            
            if user_id:
                filters["user_id"] = user_id
            
            if document_ids:
                filters["document_id"] = {"$in": document_ids}
            
            if filters:
                # Create a new vector store with filters
                filtered_vector_store = PGVectorStore.from_params(
                    database=settings.database_name,
                    host=settings.database_host,
                    password=settings.database_password,
                    port=settings.database_port,
                    user=settings.database_user,
                    table_name="llamaindex_vectors",
                    embed_dim=1536
                )
                
                # Apply filters (this is pseudo-code, actual implementation depends on PGVectorStore capabilities)
                # filtered_vector_store.set_filters(filters)
                
                return VectorStoreIndex.from_vector_store(filtered_vector_store)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to create filtered index: {e}")
            return None
    
    async def _create_query_engine_from_index(
        self, 
        index: VectorStoreIndex, 
        **kwargs
    ):
        """Create query engine from a specific index."""
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=kwargs.get("similarity_top_k", 20)
        )
        
        postprocessors = [
            SimilarityPostprocessor(
                similarity_cutoff=kwargs.get("similarity_cutoff", 0.7)
            )
        ]
        
        if kwargs.get("use_reranking", True):
            reranker = LLMRerank(
                llm=Settings.llm,
                top_n=kwargs.get("rerank_top_n", 5)
            )
            postprocessors.append(reranker)
        
        return RetrieverQueryEngine(
            retriever=retriever,
            node_postprocessors=postprocessors,
            response_mode="compact"
        )
    
    async def add_documents_from_db(
        self, 
        document_ids: List[int],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add documents from database to LlamaIndex."""
        try:
            # Fetch documents from database
            from sqlalchemy import select
            from sqlalchemy.orm import joinedload
            
            query = select(DBDocument).options(
                joinedload(DBDocument.chunks)
            ).where(DBDocument.id.in_(document_ids))
            
            if user_id:
                query = query.where(DBDocument.owner_id == user_id)
            
            result = await self.db.execute(query)
            documents = result.scalars().unique().all()
            
            # Convert to LlamaIndex documents
            llamaindex_docs = []
            for db_doc in documents:
                for chunk in db_doc.chunks:
                    doc = Document(
                        text=chunk.content,
                        metadata={
                            "document_id": db_doc.id,
                            "document_title": db_doc.title,
                            "document_type": db_doc.file_type,
                            "chunk_id": chunk.id,
                            "chunk_index": chunk.chunk_index,
                            "user_id": db_doc.owner_id,
                            "created_at": chunk.created_at.isoformat(),
                            "token_count": chunk.token_count,
                            "language": chunk.language
                        }
                    )
                    llamaindex_docs.append(doc)
            
            # Process documents through ingestion pipeline
            nodes = await self.ingestion_pipeline.arun(documents=llamaindex_docs)
            
            # Add to index
            self.index.insert_nodes(nodes)
            
            return {
                "success": True,
                "documents_processed": len(documents),
                "chunks_added": len(llamaindex_docs),
                "nodes_created": len(nodes)
            }
        
        except Exception as e:
            logger.error(f"Failed to add documents to LlamaIndex: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents_processed": 0,
                "chunks_added": 0,
                "nodes_created": 0
            }
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        user_id: Optional[int] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Perform semantic search without full RAG processing."""
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k
        )
        
        try:
            nodes = await retriever.aretrieve(query)
            
            results = []
            for node in nodes:
                # Filter by user if specified
                if user_id and node.node.metadata.get("user_id") != user_id:
                    continue
                
                result = {
                    "content": node.node.text,
                    "score": getattr(node, 'score', 0.0),
                    "node_id": node.node.node_id
                }
                
                if include_metadata:
                    result["metadata"] = node.node.metadata
                
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def get_document_summary(
        self, 
        document_id: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a summary of a specific document using LlamaIndex."""
        try:
            # Create a filtered index for just this document
            filtered_index = await self._create_filtered_index(
                user_id=user_id,
                document_ids=[document_id]
            )
            
            if not filtered_index:
                return {"error": "Document not found or access denied"}
            
            # Create a summary query engine
            summary_engine = filtered_index.as_query_engine(
                response_mode="tree_summarize",
                use_async=True
            )
            
            # Generate summary
            summary_response = await summary_engine.aquery(
                "Please provide a comprehensive summary of this document, including its main topics, key points, and conclusions."
            )
            
            return {
                "document_id": document_id,
                "summary": str(summary_response),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Document summary generation failed: {e}")
            return {"error": str(e)}
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the LlamaIndex."""
        try:
            # This would need to be implemented based on your vector store capabilities
            # For now, return basic info
            return {
                "index_type": "VectorStoreIndex",
                "vector_store": "PGVector",
                "embedding_model": settings.openai_embedding_model,
                "chunk_size": settings.llamaindex_chunk_size,
                "chunk_overlap": settings.llamaindex_chunk_overlap,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"error": str(e)}
```

## API Endpoint Modifications

### Updated Conversation API with LangChain Support

```python
# app/api/conversations.py - Modified to support LangChain
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional
import json

from app.config import settings
from app.services.conversation import ConversationService
from app.services.langchain_conversation import LangChainConversationService
from app.dependencies import get_current_user, get_db
from shared.schemas.conversation import ChatRequest, ChatResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])

async def get_conversation_service(db=Depends(get_db)):
    """Dependency to get the appropriate conversation service."""
    if settings.use_langchain:
        return LangChainConversationService(db)
    else:
        return ConversationService(db)

@router.post("/{conversation_id}/chat")
async def chat(
    conversation_id: int,
    request: ChatRequest,
    conversation_service=Depends(get_conversation_service),
    current_user=Depends(get_current_user)
):
    """Chat endpoint with LangChain/legacy routing."""
    try:
        if settings.use_langchain:
            # Use LangChain-based conversation service
            result = await conversation_service.process_chat_langchain(
                request=request,
                user_id=current_user.id,
                conversation_id=conversation_id
            )
        else:
            # Use legacy conversation service
            result = await conversation_service.process_chat(
                request=request,
                user_id=current_user.id
            )
        
        return ChatResponse(**result)
    
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )

@router.post("/{conversation_id}/chat/stream")
async def chat_stream(
    conversation_id: int,
    request: ChatRequest,
    conversation_service=Depends(get_conversation_service),
    current_user=Depends(get_current_user)
):
    """Streaming chat endpoint with LangChain support."""
    
    async def generate_stream():
        try:
            if settings.use_langchain:
                async for chunk in conversation_service.process_chat_stream_langchain(
                    request=request,
                    user_id=current_user.id,
                    conversation_id=conversation_id
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            else:
                async for chunk in conversation_service.process_chat_stream(
                    request=request,
                    user_id=current_user.id
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            
            yield "data: [DONE]\n\n"
        
        except Exception as e:
            error_chunk = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

# New endpoint for LangChain-specific features
@router.post("/{conversation_id}/chat/advanced")
async def chat_advanced(
    conversation_id: int,
    request: ChatRequest,
    use_reranking: bool = True,
    similarity_threshold: float = 0.7,
    max_sources: int = 5,
    conversation_service=Depends(get_conversation_service),
    current_user=Depends(get_current_user)
):
    """Advanced chat endpoint with LangChain/LlamaIndex features."""
    if not settings.use_langchain or not settings.use_llamaindex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Advanced chat features require LangChain and LlamaIndex to be enabled"
        )
    
    try:
        result = await conversation_service.process_advanced_chat(
            request=request,
            user_id=current_user.id,
            conversation_id=conversation_id,
            use_reranking=use_reranking,
            similarity_threshold=similarity_threshold,
            max_sources=max_sources
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Advanced chat processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced chat processing failed: {str(e)}"
        )
```

### New RAG Endpoint for LlamaIndex

```python
# app/api/rag.py - New RAG-specific endpoints
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel

from app.config import settings
from app.services.llamaindex_rag_service import LlamaIndexRAGService
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/rag", tags=["rag"])

class RAGQueryRequest(BaseModel):
    query: str
    document_ids: Optional[List[int]] = None
    use_reranking: bool = True
    similarity_threshold: float = 0.7
    max_sources: int = 10

class RAGQueryResponse(BaseModel):
    response: str
    sources: List[dict]
    query: str
    timestamp: str
    metadata: dict

@router.post("/query")
async def rag_query(
    request: RAGQueryRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
) -> RAGQueryResponse:
    """Perform RAG query using LlamaIndex."""
    if not settings.use_llamaindex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LlamaIndex is not enabled"
        )
    
    try:
        rag_service = LlamaIndexRAGService(db)
        
        result = await rag_service.query_with_context(
            query_text=request.query,
            user_id=current_user.id,
            document_ids=request.document_ids,
            use_reranking=request.use_reranking,
            similarity_cutoff=request.similarity_threshold,
            similarity_top_k=request.max_sources * 2,  # Get more, then rerank
            rerank_top_n=request.max_sources
        )
        
        return RAGQueryResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {str(e)}"
        )

@router.get("/search")
async def semantic_search(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(10, description="Number of results"),
    document_ids: Optional[List[int]] = Query(None, description="Filter by document IDs"),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Perform semantic search without full RAG processing."""
    if not settings.use_llamaindex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LlamaIndex is not enabled"
        )
    
    try:
        rag_service = LlamaIndexRAGService(db)
        
        results = await rag_service.semantic_search(
            query=query,
            top_k=top_k,
            user_id=current_user.id
        )
        
        # Filter by document IDs if provided
        if document_ids:
            results = [
                r for r in results 
                if r.get("metadata", {}).get("document_id") in document_ids
            ]
        
        return {
            "results": results,
            "query": query,
            "total_results": len(results)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}"
        )

@router.post("/documents/{document_id}/summary")
async def get_document_summary(
    document_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Generate a summary of a specific document."""
    if not settings.use_llamaindex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LlamaIndex is not enabled"
        )
    
    try:
        rag_service = LlamaIndexRAGService(db)
        
        summary = await rag_service.get_document_summary(
            document_id=document_id,
            user_id=current_user.id
        )
        
        if "error" in summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=summary["error"]
            )
        
        return summary
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document summary generation failed: {str(e)}"
        )

@router.post("/documents/ingest")
async def ingest_documents(
    document_ids: List[int],
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Ingest documents into LlamaIndex for RAG."""
    if not settings.use_llamaindex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LlamaIndex is not enabled"
        )
    
    try:
        rag_service = LlamaIndexRAGService(db)
        
        result = await rag_service.add_documents_from_db(
            document_ids=document_ids,
            user_id=current_user.id
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed: {str(e)}"
        )

@router.get("/stats")
async def get_rag_stats(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get RAG system statistics."""
    if not settings.use_llamaindex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LlamaIndex is not enabled"
        )
    
    try:
        rag_service = LlamaIndexRAGService(db)
        stats = await rag_service.get_index_stats()
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RAG stats: {str(e)}"
        )
```

## Database Integration

### Migration Script for LlamaIndex Tables

```python
# migrations/versions/add_llamaindex_support.py
"""Add LlamaIndex support tables

Revision ID: llamaindex_001
Revises: previous_revision
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector import Vector

# revision identifiers
revision = 'llamaindex_001'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Create LlamaIndex vectors table
    op.create_table(
        'llamaindex_vectors',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('metadata_', sa.JSON(), nullable=True),
        sa.Column('node_id', sa.String(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index(
        'ix_llamaindex_vectors_node_id',
        'llamaindex_vectors',
        ['node_id']
    )
    
    # Create HNSW index for vector similarity search
    op.execute("""
        CREATE INDEX llamaindex_vectors_embedding_hnsw_idx 
        ON llamaindex_vectors 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
    
    # Create IVFFlat index as alternative
    op.execute("""
        CREATE INDEX llamaindex_vectors_embedding_ivfflat_idx 
        ON llamaindex_vectors 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)
    
    # Add metadata indexes for filtering
    op.execute("""
        CREATE INDEX llamaindex_vectors_metadata_user_id_idx 
        ON llamaindex_vectors 
        USING gin ((metadata_->>'user_id'))
    """)
    
    op.execute("""
        CREATE INDEX llamaindex_vectors_metadata_document_id_idx 
        ON llamaindex_vectors 
        USING gin ((metadata_->>'document_id'))
    """)

def downgrade():
    op.drop_table('llamaindex_vectors')
```

### Extended Configuration with LangChain/LlamaIndex Settings

```python
# app/config.py - Extended configuration
from pydantic import BaseSettings, Field
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Existing settings...
    
    # Migration feature flags
    use_langchain: bool = Field(
        default=False,
        description="Enable LangChain integration"
    )
    use_llamaindex: bool = Field(
        default=False,
        description="Enable LlamaIndex integration"
    )
    migration_mode: str = Field(
        default="hybrid",
        description="Migration mode: legacy, hybrid, or new"
    )
    
    # LangChain specific settings
    langchain_verbose: bool = Field(
        default=False,
        description="Enable verbose logging for LangChain operations"
    )
    langchain_debug: bool = Field(
        default=False,
        description="Enable debug mode for LangChain"
    )
    langsmith_api_key: Optional[str] = Field(
        default=None,
        description="LangSmith API key for observability"
    )
    langsmith_project: Optional[str] = Field(
        default=None,
        description="LangSmith project name"
    )
    langchain_cache_enabled: bool = Field(
        default=True,
        description="Enable caching for LangChain operations"
    )
    
    # LlamaIndex specific settings
    llamaindex_cache_dir: str = Field(
        default="cache/llamaindex",
        description="Cache directory for LlamaIndex"
    )
    llamaindex_chunk_size: int = Field(
        default=1024,
        description="Chunk size for document splitting"
    )
    llamaindex_chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks"
    )
    llamaindex_similarity_threshold: float = Field(
        default=0.7,
        description="Default similarity threshold"
    )
    llamaindex_max_sources: int = Field(
        default=10,
        description="Maximum number of sources to retrieve"
    )
    
    # Vector store settings
    vector_store_type: str = Field(
        default="pgvector",
        description="Type of vector store to use"
    )
    vector_index_type: str = Field(
        default="hnsw",
        description="Type of vector index: hnsw or ivfflat"
    )
    hnsw_m: int = Field(
        default=16,
        description="HNSW index parameter m"
    )
    hnsw_ef_construction: int = Field(
        default=64,
        description="HNSW index parameter ef_construction"
    )
    hnsw_ef_search: int = Field(
        default=40,
        description="HNSW index parameter ef_search"
    )
    
    # Performance settings
    embedding_batch_size: int = Field(
        default=100,
        description="Batch size for embedding generation"
    )
    max_concurrent_requests: int = Field(
        default=10,
        description="Maximum concurrent API requests"
    )
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    
    # API versioning
    api_version: str = Field(
        default="v1",
        description="API version to use"
    )
    enable_legacy_endpoints: bool = Field(
        default=True,
        description="Enable legacy API endpoints"
    )
    enable_experimental_features: bool = Field(
        default=False,
        description="Enable experimental features"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Initialize LangChain/LlamaIndex configurations
def configure_langchain():
    """Configure LangChain settings."""
    if settings.use_langchain:
        os.environ["LANGCHAIN_VERBOSE"] = str(settings.langchain_verbose)
        
        if settings.langsmith_api_key:
            os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
            
        if settings.langsmith_project:
            os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project

def configure_llamaindex():
    """Configure LlamaIndex settings."""
    if settings.use_llamaindex:
        # Create cache directory
        os.makedirs(settings.llamaindex_cache_dir, exist_ok=True)
        
        # Set environment variables
        os.environ["LLAMAINDEX_CACHE_DIR"] = settings.llamaindex_cache_dir

# Configure on import
configure_langchain()
configure_llamaindex()
```

This comprehensive implementation guide provides detailed examples for all major components of the migration. The code samples show how to:

1. Implement LangChain services while maintaining backwards compatibility
2. Create advanced RAG capabilities with LlamaIndex
3. Modify API endpoints to support both legacy and new implementations
4. Handle database migrations and configurations
5. Provide comprehensive testing and monitoring

The approach ensures a smooth transition while adding powerful new capabilities to the ai-chatbot-mcp system.