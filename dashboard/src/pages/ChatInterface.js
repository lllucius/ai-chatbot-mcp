import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Send, Person, SmartToy } from '@mui/icons-material';
import axios from 'axios';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [streamingMessage, setStreamingMessage] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setError('');
    setLoading(true);

    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      // Try streaming first
      const response = await fetch('/api/conversations/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          user_message: userMessage,
          use_rag: true,
          use_tools: true,
          temperature: 0.7,
          max_tokens: 1000,
        }),
      });

      if (!response.ok) {
        throw new Error('Streaming failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      let aiMessageId = Date.now() + 1;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'content') {
                fullResponse += data.content;
                setStreamingMessage(fullResponse);
              } else if (data.type === 'complete') {
                // Add final AI message
                const aiMessage = {
                  id: aiMessageId,
                  role: 'assistant',
                  content: fullResponse,
                  timestamp: new Date(),
                  rag_context: data.response?.rag_context,
                  tool_calls: data.response?.tool_call_summary?.successful_calls || [],
                };
                setMessages(prev => [...prev, aiMessage]);
                setStreamingMessage('');
                break;
              } else if (data.type === 'error') {
                throw new Error(data.error);
              }
            } catch (e) {
              // Ignore JSON parsing errors for incomplete chunks
            }
          }
        }
      }
    } catch (streamError) {
      // Fallback to regular non-streaming API
      try {
        const response = await axios.post('/api/conversations/chat', {
          user_message: userMessage,
          use_rag: true,
          use_tools: true,
          temperature: 0.7,
          max_tokens: 1000,
        });

        const aiMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.data.ai_message.content,
          timestamp: new Date(),
          rag_context: response.data.rag_context,
          tool_calls: response.data.tool_call_summary?.successful_calls || [],
        };
        setMessages(prev => [...prev, aiMessage]);
      } catch (fallbackError) {
        setError('Failed to send message. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <Box sx={{ height: '80vh', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h4" gutterBottom>
        AI Chat Assistant
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Messages Area */}
      <Paper 
        elevation={1} 
        sx={{ 
          flex: 1, 
          mb: 2, 
          overflow: 'auto',
          p: 1,
          backgroundColor: '#fafafa'
        }}
      >
        <List sx={{ height: '100%', overflow: 'auto' }}>
          {messages.length === 0 && (
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              height: '100%',
              flexDirection: 'column'
            }}>
              <SmartToy sx={{ fontSize: 60, color: 'primary.light', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Start a conversation with the AI assistant
              </Typography>
            </Box>
          )}

          {messages.map((message) => (
            <ListItem key={message.id} alignItems="flex-start" sx={{ mb: 1 }}>
              <Avatar sx={{ mr: 2, bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main' }}>
                {message.role === 'user' ? <Person /> : <SmartToy />}
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  {message.content}
                </Typography>
                {message.rag_context && message.rag_context.length > 0 && (
                  <Box sx={{ mb: 1 }}>
                    <Chip 
                      size="small" 
                      label={`Used ${message.rag_context.length} document(s)`}
                      color="info"
                      variant="outlined"
                    />
                  </Box>
                )}
                {message.tool_calls && message.tool_calls.length > 0 && (
                  <Box sx={{ mb: 1 }}>
                    <Chip 
                      size="small" 
                      label={`${message.tool_calls.length} tool call(s)`}
                      color="success"
                      variant="outlined"
                    />
                  </Box>
                )}
                <Typography variant="caption" color="text.secondary">
                  {message.timestamp.toLocaleTimeString()}
                </Typography>
              </Box>
            </ListItem>
          ))}

          {/* Streaming message */}
          {streamingMessage && (
            <ListItem alignItems="flex-start" sx={{ mb: 1, opacity: 0.8 }}>
              <Avatar sx={{ mr: 2, bgcolor: 'secondary.main' }}>
                <SmartToy />
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  {streamingMessage}
                  <Box component="span" sx={{ 
                    display: 'inline-block',
                    width: '8px',
                    height: '12px',
                    backgroundColor: 'primary.main',
                    ml: 1,
                    animation: 'blink 1s infinite'
                  }}>
                    |
                  </Box>
                </Typography>
                <Chip 
                  size="small" 
                  label="Typing..."
                  color="primary"
                  variant="outlined"
                />
              </Box>
            </ListItem>
          )}

          <div ref={messagesEndRef} />
        </List>
      </Paper>

      {/* Input Area */}
      <Paper elevation={1} sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Type your message here..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
            variant="outlined"
            size="small"
          />
          <Button
            variant="contained"
            endIcon={loading ? <CircularProgress size={20} /> : <Send />}
            onClick={sendMessage}
            disabled={!inputMessage.trim() || loading}
            sx={{ minWidth: 120 }}
          >
            {loading ? 'Sending' : 'Send'}
          </Button>
        </Box>
      </Paper>

      <style jsx>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </Box>
  );
};

export default ChatInterface;