# AI Chatbot MCP TypeScript SDK

A comprehensive TypeScript SDK for the AI Chatbot MCP (Model Context Protocol) API. This SDK provides type-safe access to all API endpoints with modern TypeScript features, automatic authentication management, and full IDE support.

## Features

- 🚀 **Complete API Coverage** - Access to all API endpoints
- 🔒 **Type Safety** - Full TypeScript support with comprehensive type definitions
- 🔐 **Authentication** - Automatic token management and refresh
- 📦 **Modern Architecture** - Modular client design with clean separation of concerns
- 🌐 **Cross-Platform** - Works in both browser and Node.js environments
- 📝 **Rich Documentation** - Extensive JSDoc comments and usage examples
- ⚡ **Streaming Support** - Real-time chat streaming capabilities
- 🛠 **Error Handling** - Comprehensive error handling with detailed error information

## Installation

```bash
npm install @ai-chatbot-mcp/sdk
# or
yarn add @ai-chatbot-mcp/sdk
# or
pnpm add @ai-chatbot-mcp/sdk
```

## Quick Start

```typescript
import { AiChatbotSdk } from '@ai-chatbot-mcp/sdk';

// Initialize the SDK
const sdk = new AiChatbotSdk({
  baseUrl: 'https://your-api-server.com',
  timeout: 30000, // 30 seconds
});

// Authenticate
const token = await sdk.auth.login({
  username: 'your-username',
  password: 'your-password'
});

console.log('Authenticated successfully!', token);

// Create a conversation
const conversation = await sdk.conversations.create({
  title: 'My First Conversation'
});

// Send a message
const response = await sdk.conversations.chat({
  conversation_id: conversation.id,
  message: 'Hello, how can you help me today?'
});

console.log('AI Response:', response.message.content);
```

## API Reference

### Authentication

```typescript
// Login
const token = await sdk.auth.login({ username: 'user', password: 'pass' });

// Get current user
const user = await sdk.auth.me();

// Logout
await sdk.auth.logout();

// Check authentication status
if (sdk.auth.isAuthenticated()) {
  console.log('User is authenticated');
}
```

### Conversations

```typescript
// Create a conversation
const conversation = await sdk.conversations.create({
  title: 'Customer Support Chat'
});

// List conversations
const conversations = await sdk.conversations.list({
  page: 1,
  size: 20,
  active_only: true
});

// Send a chat message
const chatResponse = await sdk.conversations.chat({
  conversation_id: conversation.id,
  message: 'What are the latest features?',
  use_rag: true,
  enable_tools: true
});

// Stream chat responses
const stream = await sdk.conversations.chatStream({
  conversation_id: conversation.id,
  message: 'Tell me a long story'
});

for await (const chunk of stream) {
  console.log('Received:', chunk);
}

// Get conversation messages
const messages = await sdk.conversations.getMessages(conversation.id);

// Search conversations
const searchResults = await sdk.conversations.search({
  query: 'machine learning',
  search_messages: true,
  limit: 10
});
```

### Documents

```typescript
// Upload a document
const file = new File(['content'], 'document.txt', { type: 'text/plain' });
const document = await sdk.documents.upload(file, {
  title: 'My Document',
  process_immediately: true
});

// List documents
const documents = await sdk.documents.list({
  page: 1,
  size: 20,
  status: 'completed'
});

// Get document details
const doc = await sdk.documents.get(document.id);

// Check processing status
const status = await sdk.documents.getStatus(document.id);

// Download document
const blob = await sdk.documents.download(document.id);

// Delete document
await sdk.documents.delete(document.id);
```

### Search

```typescript
// Vector search
const vectorResults = await sdk.search.vectorSearch('machine learning', 10);

// Keyword search
const keywordResults = await sdk.search.keywordSearch('API documentation', 10);

// Hybrid search (combines vector and keyword)
const hybridResults = await sdk.search.hybridSearch('best practices', 20);

// Advanced search with custom parameters
const advancedResults = await sdk.search.search({
  query: 'neural networks',
  algorithm: 'hybrid',
  limit: 15,
  min_score: 0.7,
  document_type: 'pdf'
});

// Find similar chunks
const similarChunks = await sdk.search.findSimilarChunks(123, 5);

// Get search suggestions
const suggestions = await sdk.search.getSuggestions('machine', 5);
```

### MCP Tools and Servers

```typescript
// List MCP servers
const servers = await sdk.mcp.listServers({
  enabled_only: true,
  connected_only: true
});

// Add a new MCP server
const newServer = await sdk.mcp.addServer({
  name: 'my-tool-server',
  url: 'http://localhost:3001',
  description: 'Custom tools server',
  enabled: true
});

// Test server connection
const testResult = await sdk.mcp.testServer('my-tool-server');

// List available tools
const tools = await sdk.mcp.listTools({
  enabled_only: true
});

// Enable/disable tools
await sdk.mcp.enableTool('file-reader');
await sdk.mcp.disableTool('web-scraper');

// Test tool execution
const toolResult = await sdk.mcp.testTool('calculator', {
  operation: 'add',
  a: 5,
  b: 3
});

// Get MCP statistics
const mcpStats = await sdk.mcp.getStats();

// Refresh server connections
await sdk.mcp.refreshAll();
```

### LLM Profiles

```typescript
// List LLM profiles
const profiles = await sdk.profiles.list({
  active_only: true
});

// Get specific profile
const profile = await sdk.profiles.get('gpt-4-creative');

// Create new profile
const newProfile = await sdk.profiles.create({
  name: 'custom-profile',
  description: 'My custom LLM settings',
  model: 'gpt-4',
  parameters: {
    temperature: 0.8,
    max_tokens: 2000,
    top_p: 0.9
  }
});

// Set as default
await sdk.profiles.setDefault('custom-profile');

// Get profile statistics
const profileStats = await sdk.profiles.getStats();
```

### Prompts

```typescript
// List prompts
const prompts = await sdk.prompts.list({
  active_only: true,
  category: 'assistant'
});

// Get specific prompt
const prompt = await sdk.prompts.get('helpful-assistant');

// Create new prompt
const newPrompt = await sdk.prompts.create({
  name: 'code-reviewer',
  description: 'Code review assistant',
  template: 'You are a helpful code reviewer. Review the following code:\n\n{code}',
  category: 'development'
});

// Set as default
await sdk.prompts.setDefault('code-reviewer');

// Get categories
const categories = await sdk.prompts.getCategories();
```

### User Management

```typescript
// Update current user profile
const updatedUser = await sdk.users.updateMe({
  email: 'new-email@example.com',
  full_name: 'John Smith'
});

// Change password
await sdk.users.changePassword({
  current_password: 'old-password',
  new_password: 'new-secure-password'
});

// List all users (admin only)
const allUsers = await sdk.users.list({
  page: 1,
  size: 50,
  active_only: true
});

// Get user by ID (admin only)
const user = await sdk.users.getById('user-uuid');

// Admin operations
await sdk.users.activate('user-uuid');
await sdk.users.promote('user-uuid');  // Make superuser
await sdk.users.resetPassword('user-uuid', 'temp-password');
```

### Health and Analytics

```typescript
// Basic health check
const health = await sdk.health.basic();

// Comprehensive health status
const systemStatus = await sdk.health.comprehensive();

// Database health
const dbHealth = await sdk.health.database();

// System metrics
const metrics = await sdk.health.metrics();

// Analytics overview
const overview = await sdk.analytics.getOverview();

// Usage analytics
const usage = await sdk.analytics.getUsage({
  period: '30d',
  detailed: true
});

// Performance analytics
const performance = await sdk.analytics.getPerformance();

// Export analytics report
const report = await sdk.analytics.exportReport({
  output: 'json',
  details: true
});
```

## Configuration

```typescript
const sdk = new AiChatbotSdk({
  baseUrl: 'https://api.example.com',  // Required
  token: 'your-jwt-token',             // Optional: set later via auth
  timeout: 30000,                      // Optional: request timeout in ms
  headers: {                           // Optional: custom headers
    'X-Custom-Header': 'value'
  },
  onError: (error) => {                // Optional: global error handler
    console.error('SDK Error:', error);
  }
});
```

## Error Handling

```typescript
import { ApiError } from '@ai-chatbot-mcp/sdk';

try {
  const response = await sdk.conversations.chat({
    conversation_id: 'invalid-id',
    message: 'Hello'
  });
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', {
      status: error.status,
      statusText: error.statusText,
      url: error.url,
      response: error.response
    });
  } else {
    console.error('Unexpected error:', error);
  }
}
```

## Browser Usage

The SDK works seamlessly in browser environments:

```html
<!DOCTYPE html>
<html>
<head>
  <script type="module">
    import { AiChatbotSdk } from 'https://cdn.skypack.dev/@ai-chatbot-mcp/sdk';
    
    const sdk = new AiChatbotSdk({
      baseUrl: 'https://api.example.com'
    });
    
    // Use the SDK...
  </script>
</head>
</html>
```

## Node.js Usage

For Node.js applications, you may need to configure the base URL from environment variables:

```typescript
import { AiChatbotSdk } from '@ai-chatbot-mcp/sdk';

const sdk = new AiChatbotSdk({
  baseUrl: process.env.AI_CHATBOT_API_URL || 'http://localhost:8000',
  timeout: 60000  // Longer timeout for server-side usage
});
```

## TypeScript Support

The SDK is written in TypeScript and provides comprehensive type definitions:

```typescript
import { 
  AiChatbotSdk, 
  ChatRequest, 
  ChatResponse, 
  Conversation,
  Document,
  SearchRequest,
  ApiError 
} from '@ai-chatbot-mcp/sdk';

// All types are fully typed and provide excellent IDE support
const chatRequest: ChatRequest = {
  conversation_id: 'uuid',
  message: 'Hello',
  use_rag: true,
  enable_tools: false
};

const response: ChatResponse = await sdk.conversations.chat(chatRequest);
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue on the GitHub repository or contact the development team.