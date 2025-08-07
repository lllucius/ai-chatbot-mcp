/**
 * Example usage of the AI Chatbot MCP TypeScript SDK
 */

import { AiChatbotSdk } from './src/index';

async function main() {
  // Initialize the SDK
  const sdk = new AiChatbotSdk({
    baseUrl: 'http://localhost:8000',
    timeout: 30000,
    onError: (error) => {
      console.error('SDK Error:', error.message);
    }
  });

  try {
    // Health check
    console.log('🏥 Checking API health...');
    const health = await sdk.ping();
    console.log('✅ API is healthy:', health);

    // Authentication example
    console.log('\n🔐 Authenticating...');
    const token = await sdk.auth.login({
      username: 'demo_user',
      password: 'demo_password'
    });
    console.log('✅ Authenticated:', token.access_token?.substring(0, 20) + '...');

    // Get current user
    const user = await sdk.auth.me();
    console.log('👤 Current user:', user.username, user.email);

    // List conversations
    console.log('\n💬 Fetching conversations...');
    const conversations = await sdk.conversations.list({ page: 1, size: 5 });
    console.log(`📋 Found ${conversations.items.length} conversations`);

    // Create a new conversation if none exist
    let conversation;
    if (conversations.items.length === 0) {
      console.log('📝 Creating new conversation...');
      conversation = await sdk.conversations.create({
        title: 'SDK Test Conversation'
      });
      console.log('✅ Created conversation:', conversation.id);
    } else {
      conversation = conversations.items[0];
      console.log('📝 Using existing conversation:', conversation.id);
    }

    // Send a chat message
    console.log('\n🤖 Sending chat message...');
    const chatResponse = await sdk.conversations.chat({
      conversation_id: conversation.id,
      message: 'Hello! Can you tell me about the capabilities of this system?',
      use_rag: true,
      enable_tools: true
    });
    console.log('💬 AI Response:', chatResponse.message.content);

    // List documents
    console.log('\n📄 Fetching documents...');
    const documents = await sdk.documents.list({ page: 1, size: 5 });
    console.log(`📚 Found ${documents.items.length} documents`);

    // Search example
    if (documents.items.length > 0) {
      console.log('\n🔍 Performing search...');
      const searchResults = await sdk.search.hybridSearch('capabilities', 5);
      console.log(`🎯 Found ${searchResults.results.length} search results`);
    }

    // List MCP servers
    console.log('\n🔧 Checking MCP servers...');
    const mcpServers = await sdk.mcp.listServers();
    console.log(`⚙️ Found ${mcpServers.length} MCP servers`);

    // List LLM profiles
    console.log('\n🧠 Fetching LLM profiles...');
    const profiles = await sdk.profiles.list();
    console.log(`🎛️ Found ${profiles.items.length} LLM profiles`);

    // List prompts
    console.log('\n📝 Fetching prompts...');
    const prompts = await sdk.prompts.list();
    console.log(`📜 Found ${prompts.items.length} prompts`);

    // Get system analytics
    console.log('\n📊 Fetching analytics...');
    const analytics = await sdk.analytics.getOverview();
    console.log('📈 Analytics overview:', analytics);

    console.log('\n✅ SDK example completed successfully!');

  } catch (error) {
    console.error('❌ Example failed:', error);
    process.exit(1);
  }
}

// Run the example
if (require.main === module) {
  main().catch(console.error);
}

export default main;