import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  Switch,
  FormControlLabel,
  CircularProgress,
  Alert,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  Settings as SettingsIcon,
  AccessTime as TimeIcon,
  Memory as TokenIcon,
} from '@mui/icons-material';
import { ConversationService } from '../services';
import { useAuth } from '../services/AuthContext';
import { Conversation, Message, ChatRequest } from '../types';

const ChatInterface: React.FC = () => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  
  // Chat settings
  const [useRag, setUseRag] = useState(true);
  const [enableTools, setEnableTools] = useState(true);
  const [temperature, setTemperature] = useState(0.7);
  
  // Metrics
  const [lastRequestTime, setLastRequestTime] = useState<number>(0);
  const [lastTokenCount, setLastTokenCount] = useState<number>(0);
  const [lastResponseTime, setLastResponseTime] = useState<number>(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load messages when conversation changes
  useEffect(() => {
    if (currentConversation) {
      loadMessages(currentConversation.id);
    }
  }, [currentConversation]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversations = async () => {
    try {
      const response = await ConversationService.listConversations({ page: 1, size: 50 });
      if (response.success && response.data) {
        setConversations(response.data.items);
        if (response.data.items.length > 0 && !currentConversation) {
          setCurrentConversation(response.data.items[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
      setError('Failed to load conversations');
    }
  };

  const loadMessages = async (conversationId: string) => {
    try {
      const response = await ConversationService.getMessages(conversationId, { page: 1, size: 100 });
      if (response.success && response.data) {
        setMessages(response.data.items.reverse()); // Reverse to show newest at bottom
      }
    } catch (error) {
      console.error('Failed to load messages:', error);
      setError('Failed to load messages');
    }
  };

  const createNewConversation = async () => {
    try {
      const response = await ConversationService.createConversation({
        title: 'New Conversation',
        is_active: true,
      });
      if (response.success && response.data) {
        const newConv = response.data;
        setConversations(prev => [newConv, ...prev]);
        setCurrentConversation(newConv);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to create conversation:', error);
      setError('Failed to create new conversation');
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    setIsLoading(true);
    setIsStreaming(true);
    setError(null);
    setStreamingContent('');
    
    const startTime = Date.now();
    const userMessage = newMessage;
    setNewMessage('');

    try {
      const chatRequest: ChatRequest = {
        message: userMessage,
        conversation_id: currentConversation?.id,
        conversation_title: currentConversation?.title || 'New Chat',
        use_rag: useRag,
        enable_tools: enableTools,
        temperature: temperature,
        tool_handling_mode: 'complete_with_results',
      };

      // Add user message immediately
      const tempUserMessage: Message = {
        id: `temp-${Date.now()}`,
        content: userMessage,
        role: 'user',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        token_count: 0,
        response_time: 0,
      };
      setMessages(prev => [...prev, tempUserMessage]);

      await ConversationService.streamChat(
        chatRequest,
        (chunk: any) => {
          // Handle streaming chunks
          if (chunk.type === 'content') {
            setStreamingContent(prev => prev + chunk.content);
          } else if (chunk.type === 'tool_call') {
            console.log('Tool call:', chunk.tool, chunk.result);
          }
        },
        (response: any) => {
          // Handle completion
          const endTime = Date.now();
          const responseTime = endTime - startTime;
          
          setLastRequestTime(startTime);
          setLastResponseTime(responseTime);
          setLastTokenCount(response.ai_message?.token_count || 0);
          
          // Add AI message
          if (response.ai_message) {
            setMessages(prev => [...prev.slice(0, -1), response.message, response.ai_message]);
          }
          
          // Update conversation
          if (response.conversation) {
            setCurrentConversation(response.conversation);
            setConversations(prev => 
              prev.map(conv => 
                conv.id === response.conversation.id 
                  ? response.conversation 
                  : conv
              )
            );
          }
          
          setStreamingContent('');
          setIsStreaming(false);
          setIsLoading(false);
        },
        (error: string) => {
          setError(error);
          setIsStreaming(false);
          setIsLoading(false);
          // Remove temporary user message on error
          setMessages(prev => prev.slice(0, -1));
          setNewMessage(userMessage); // Restore message
        }
      );

    } catch (error: any) {
      console.error('Chat error:', error);
      setError('Failed to send message');
      setIsStreaming(false);
      setIsLoading(false);
      setMessages(prev => prev.slice(0, -1));
      setNewMessage(userMessage);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <>
      <style>
        {`
          @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
          }
        `}
      </style>
      <Box sx={{ height: '80vh', display: 'flex', gap: 2 }}>
      {/* Conversations Sidebar */}
      <Paper sx={{ width: 300, p: 2, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Conversations</Typography>
          <IconButton onClick={createNewConversation} size="small">
            <SendIcon />
          </IconButton>
        </Box>
        
        <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          {conversations.map((conv) => (
            <Paper
              key={conv.id}
              sx={{
                p: 1,
                mb: 1,
                cursor: 'pointer',
                bgcolor: currentConversation?.id === conv.id ? 'primary.light' : 'grey.50',
                '&:hover': { bgcolor: 'grey.100' },
              }}
              onClick={() => setCurrentConversation(conv)}
            >
              <Typography variant="body2" noWrap>
                {conv.title}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {conv.message_count} messages
              </Typography>
            </Paper>
          ))}
        </Box>

        {/* Chat Settings */}
        <Divider sx={{ my: 2 }} />
        <Typography variant="subtitle2" gutterBottom>
          <SettingsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
          Settings
        </Typography>
        
        <FormControlLabel
          control={<Switch checked={useRag} onChange={(e) => setUseRag(e.target.checked)} />}
          label="Use RAG"
          sx={{ mb: 1 }}
        />
        
        <FormControlLabel
          control={<Switch checked={enableTools} onChange={(e) => setEnableTools(e.target.checked)} />}
          label="Enable Tools"
          sx={{ mb: 1 }}
        />
        
        <FormControl size="small">
          <InputLabel>Temperature</InputLabel>
          <Select
            value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
            label="Temperature"
          >
            <MenuItem value={0.1}>0.1 (Focused)</MenuItem>
            <MenuItem value={0.3}>0.3 (Balanced)</MenuItem>
            <MenuItem value={0.7}>0.7 (Creative)</MenuItem>
            <MenuItem value={1.0}>1.0 (Very Creative)</MenuItem>
          </Select>
        </FormControl>
        
        {/* Metrics Display */}
        <Divider sx={{ my: 2 }} />
        <Typography variant="subtitle2" gutterBottom>
          Performance Metrics
        </Typography>
        
        <Grid container spacing={1}>
          <Grid item xs={12}>
            <Card variant="outlined" sx={{ p: 1 }}>
              <Box display="flex" alignItems="center" gap={1}>
                <TimeIcon fontSize="small" color="primary" />
                <Typography variant="caption">
                  Response Time: {lastResponseTime > 0 ? `${lastResponseTime}ms` : 'N/A'}
                </Typography>
              </Box>
            </Card>
          </Grid>
          <Grid item xs={12}>
            <Card variant="outlined" sx={{ p: 1 }}>
              <Box display="flex" alignItems="center" gap={1}>
                <TokenIcon fontSize="small" color="secondary" />
                <Typography variant="caption">
                  Tokens: {lastTokenCount > 0 ? lastTokenCount : 'N/A'}
                </Typography>
              </Box>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Chat Area */}
      <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Chat Header */}
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">
            {currentConversation?.title || 'Select a conversation'}
          </Typography>
          {currentConversation && (
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              {useRag && <Chip label="RAG Enabled" size="small" color="primary" />}
              {enableTools && <Chip label="Tools Enabled" size="small" color="secondary" />}
              <Chip label={`Temp: ${temperature}`} size="small" variant="outlined" />
            </Box>
          )}
        </Box>

        {/* Messages Area */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                display: 'flex',
                mb: 2,
                alignItems: 'flex-start',
                flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              <Avatar
                sx={{
                  mx: 1,
                  bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                }}
              >
                {message.role === 'user' ? <PersonIcon /> : <BotIcon />}
              </Avatar>
              
              <Paper
                sx={{
                  p: 2,
                  maxWidth: '70%',
                  bgcolor: message.role === 'user' ? 'primary.light' : 'grey.50',
                }}
              >
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {message.content}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {formatTimestamp(message.created_at)}
                  {message.token_count && ` • ${message.token_count} tokens`}
                </Typography>
              </Paper>
            </Box>
          ))}
          
          {/* Streaming Content */}
          {isStreaming && streamingContent && (
            <Box
              sx={{
                display: 'flex',
                mb: 2,
                alignItems: 'flex-start',
                flexDirection: 'row',
              }}
            >
              <Avatar sx={{ mx: 1, bgcolor: 'secondary.main' }}>
                <BotIcon />
              </Avatar>
              
              <Paper sx={{ p: 2, maxWidth: '70%', bgcolor: 'grey.50' }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {streamingContent}
                  <Box component="span" sx={{ animation: 'blink 1s infinite' }}>|</Box>
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Streaming...
                </Typography>
              </Paper>
            </Box>
          )}
          
          {isLoading && !isStreaming && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Avatar sx={{ bgcolor: 'secondary.main' }}>
                <BotIcon />
              </Avatar>
              <CircularProgress size={20} />
              <Typography variant="body2" color="text.secondary">
                AI is thinking...
              </Typography>
            </Box>
          )}
          
          <div ref={messagesEndRef} />
        </Box>

        {/* Message Input */}
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
              disabled={isLoading || !currentConversation}
              variant="outlined"
            />
            <IconButton
              onClick={sendMessage}
              disabled={!newMessage.trim() || isLoading}
              color="primary"
              sx={{ alignSelf: 'flex-end' }}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Box>
      </Paper>
    </Box>
    </>
  );
};

export default ChatInterface;