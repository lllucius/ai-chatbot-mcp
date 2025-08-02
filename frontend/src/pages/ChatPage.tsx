/**
 * Chat Page Component
 * 
 * This is the main chat interface for the AI Chatbot. It provides:
 * - Real-time conversation with AI assistant
 * - Message history with pagination
 * - LLM profile and prompt selection
 * - RAG (Retrieval-Augmented Generation) options
 * - Document context integration
 * - Conversation management (create, save, delete)
 * - Typing indicators and message status
 * - Copy, share, and export functionality
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Stack,
  Avatar,
  List,
  ListItem,
  Chip,
  Button,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Tooltip,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Collapse,
} from '@mui/material';
import {
  Send as SendIcon,
  Add as AddIcon,
  Settings as SettingsIcon,
  ContentCopy as CopyIcon,
  Share as ShareIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Psychology as AiIcon,
  Person as UserIcon,
  Description as DocumentIcon,
  TrendingUp as StatsIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';

import { PageHeader, LoadingSpinner, StatusChip, ConfirmDialog } from '../components/common/CommonComponents';
import { useAuth } from '../contexts/AuthContext';
import {
  useConversation,
  useConversationMessages,
  useSendMessage,
  useCreateConversation,
  useUpdateConversation,
  useDeleteConversation,
  useLlmProfiles,
  usePromptTemplates,
} from '../hooks/api';
import type { Message, ChatRequest, LlmProfile, PromptTemplate } from '../types/api';

// =============================================================================
// Chat Message Component
// =============================================================================

/**
 * Props for ChatMessage component
 */
interface ChatMessageProps {
  message: Message;
  onCopy?: (content: string) => void;
}

/**
 * Individual chat message component with user/AI styling
 */
function ChatMessage({ message, onCopy }: ChatMessageProps): React.ReactElement {
  const [expanded, setExpanded] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    onCopy?.(message.content);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <ListItem
      sx={{
        flexDirection: 'column',
        alignItems: message.is_user ? 'flex-end' : 'flex-start',
        px: 1,
        py: 0.5,
      }}
    >
      <Box
        sx={{
          maxWidth: '70%',
          minWidth: '200px',
        }}
      >
        {/* Message Header */}
        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5 }}>
          <Avatar
            sx={{
              width: 32,
              height: 32,
              bgcolor: message.is_user ? 'primary.main' : 'secondary.main',
            }}
          >
            {message.is_user ? <UserIcon /> : <AiIcon />}
          </Avatar>
          <Typography variant="caption" color="text.secondary">
            {message.is_user ? 'You' : 'AI Assistant'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {formatTimestamp(message.created_at)}
          </Typography>
        </Stack>

        {/* Message Content */}
        <Paper
          elevation={1}
          sx={{
            p: 2,
            bgcolor: message.is_user ? 'primary.50' : 'grey.50',
            border: 1,
            borderColor: message.is_user ? 'primary.200' : 'grey.200',
            borderRadius: 2,
            position: 'relative',
          }}
        >
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {message.content}
          </Typography>

          {/* Message Actions */}
          <Stack direction="row" spacing={1} sx={{ mt: 1, justifyContent: 'flex-end' }}>
            <Tooltip title="Copy message">
              <IconButton size="small" onClick={handleCopy}>
                <CopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            {!message.is_user && message.token_usage && (
              <Tooltip title="Show details">
                <IconButton 
                  size="small" 
                  onClick={() => setExpanded(!expanded)}
                >
                  {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                </IconButton>
              </Tooltip>
            )}
          </Stack>

          {/* Expandable Details for AI Messages */}
          {!message.is_user && (
            <Collapse in={expanded}>
              <Divider sx={{ my: 1 }} />
              <Stack spacing={1}>
                {/* Token Usage */}
                {message.token_usage && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Token Usage:
                    </Typography>
                    <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                      <Chip
                        label={`Prompt: ${message.token_usage.prompt_tokens}`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`Response: ${message.token_usage.completion_tokens}`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`Total: ${message.token_usage.total_tokens}`}
                        size="small"
                        variant="outlined"
                        color="primary"
                      />
                    </Stack>
                  </Box>
                )}

                {/* RAG Context */}
                {message.rag_context && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Document Sources ({message.rag_context.documents_retrieved}):
                    </Typography>
                    <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                      {message.rag_context.sources.map((source, index) => (
                        <Card key={index} variant="outlined" sx={{ p: 1 }}>
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <DocumentIcon fontSize="small" color="action" />
                            <Typography variant="caption" sx={{ fontWeight: 500 }}>
                              {source.document_title}
                            </Typography>
                            <Chip
                              label={`${Math.round(source.similarity_score * 100)}%`}
                              size="small"
                              color="success"
                              variant="outlined"
                            />
                          </Stack>
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                            {source.chunk_content.substring(0, 100)}...
                          </Typography>
                        </Card>
                      ))}
                    </Stack>
                  </Box>
                )}
              </Stack>
            </Collapse>
          )}
        </Paper>
      </Box>
    </ListItem>
  );
}

// =============================================================================
// Chat Settings Panel Component
// =============================================================================

/**
 * Props for ChatSettings component
 */
interface ChatSettingsProps {
  useRag: boolean;
  onUseRagChange: (value: boolean) => void;
  selectedProfile: string;
  onProfileChange: (profile: string) => void;
  selectedPrompt: string;
  onPromptChange: (prompt: string) => void;
  profiles: LlmProfile[];
  prompts: PromptTemplate[];
  expanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
}

/**
 * Chat settings panel for configuring AI behavior
 */
function ChatSettings({
  useRag,
  onUseRagChange,
  selectedProfile,
  onProfileChange,
  selectedPrompt,
  onPromptChange,
  profiles,
  prompts,
  expanded,
  onExpandedChange,
}: ChatSettingsProps): React.ReactElement {
  return (
    <Card>
      <CardContent sx={{ pb: expanded ? 2 : 1, '&:last-child': { pb: expanded ? 2 : 1 } }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="subtitle2">Chat Settings</Typography>
          <IconButton onClick={() => onExpandedChange(!expanded)} size="small">
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Stack>

        <Collapse in={expanded}>
          <Stack spacing={2} sx={{ mt: 2 }}>
            {/* RAG Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={useRag}
                  onChange={(e) => onUseRagChange(e.target.checked)}
                />
              }
              label={
                <Box>
                  <Typography variant="body2">Use RAG (Document Search)</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Include relevant documents in AI responses
                  </Typography>
                </Box>
              }
            />

            {/* LLM Profile Selection */}
            <FormControl fullWidth size="small">
              <InputLabel>LLM Profile</InputLabel>
              <Select
                value={selectedProfile}
                onChange={(e) => onProfileChange(e.target.value)}
                label="LLM Profile"
              >
                <MenuItem value="">
                  <em>Default</em>
                </MenuItem>
                {profiles.map((profile) => (
                  <MenuItem key={profile.id} value={profile.name}>
                    <Box>
                      <Typography variant="body2">{profile.title}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Temp: {profile.parameters.temperature}, Max Tokens: {profile.parameters.max_tokens}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Prompt Template Selection */}
            <FormControl fullWidth size="small">
              <InputLabel>Prompt Template</InputLabel>
              <Select
                value={selectedPrompt}
                onChange={(e) => onPromptChange(e.target.value)}
                label="Prompt Template"
              >
                <MenuItem value="">
                  <em>Default</em>
                </MenuItem>
                {prompts.map((prompt) => (
                  <MenuItem key={prompt.id} value={prompt.name}>
                    <Box>
                      <Typography variant="body2">{prompt.title}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {prompt.category} • {prompt.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </Collapse>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Main Chat Page Component
// =============================================================================

/**
 * Main chat page component
 */
export default function ChatPage(): React.ReactElement {
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  // State for message input and settings
  const [messageInput, setMessageInput] = useState('');
  const [useRag, setUseRag] = useState(true);
  const [selectedProfile, setSelectedProfile] = useState('');
  const [selectedPrompt, setSelectedPrompt] = useState('');
  const [settingsExpanded, setSettingsExpanded] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Refs for auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // API hooks
  const { data: conversation, isLoading: conversationLoading } = useConversation(
    conversationId || ''
  );
  
  const { 
    data: messagesData, 
    isLoading: messagesLoading,
    refetch: refetchMessages,
  } = useConversationMessages(
    conversationId || '',
    1,
    50
  );

  const sendMessageMutation = useSendMessage();
  const createConversationMutation = useCreateConversation();
  const updateConversationMutation = useUpdateConversation();
  const deleteConversationMutation = useDeleteConversation();

  const { data: profiles = [] } = useLlmProfiles();
  const { data: prompts = [] } = usePromptTemplates();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messagesData?.items]);

  /**
   * Handle sending a new message
   */
  const handleSendMessage = async () => {
    if (!messageInput.trim()) return;

    const messageContent = messageInput.trim();
    setMessageInput('');

    try {
      // Create chat request
      const chatRequest: ChatRequest = {
        user_message: messageContent,
        conversation_id: conversationId,
        use_rag: useRag,
        profile_name: selectedProfile || undefined,
        prompt_name: selectedPrompt || undefined,
      };

      const response = await sendMessageMutation.mutateAsync(chatRequest);

      // If this is a new conversation, navigate to it
      if (!conversationId && response.conversation.id) {
        navigate(`/chat/${response.conversation.id}`, { replace: true });
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  /**
   * Handle starting a new conversation
   */
  const handleNewConversation = async () => {
    try {
      const newConversation = await createConversationMutation.mutateAsync('New Conversation');
      navigate(`/chat/${newConversation.id}`);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  /**
   * Handle deleting current conversation
   */
  const handleDeleteConversation = async () => {
    if (!conversationId) return;

    try {
      await deleteConversationMutation.mutateAsync(conversationId);
      navigate('/chat');
      setDeleteDialogOpen(false);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  /**
   * Handle Enter key press in message input
   */
  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  /**
   * Handle copying message content
   */
  const handleCopyMessage = (content: string) => {
    // You could show a toast notification here
    console.log('Message copied to clipboard');
  };

  const messages = messagesData?.items || [];
  const isLoading = conversationLoading || messagesLoading;
  const isSending = sendMessageMutation.isPending;

  return (
    <Box sx={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
      <PageHeader
        title={conversation?.title || 'Chat'}
        subtitle="Have a conversation with your AI assistant"
        actions={
          <Stack direction="row" spacing={1}>
            {conversationId && (
              <>
                <Tooltip title="Delete conversation">
                  <IconButton 
                    onClick={() => setDeleteDialogOpen(true)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
                <Divider orientation="vertical" flexItem />
              </>
            )}
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleNewConversation}
              disabled={createConversationMutation.isPending}
            >
              New Chat
            </Button>
          </Stack>
        }
      />

      <Box sx={{ display: 'flex', gap: 2, height: '100%' }}>
        {/* Main Chat Area */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Messages Area */}
          <Paper 
            sx={{ 
              flex: 1, 
              display: 'flex', 
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {isLoading ? (
              <LoadingSpinner message="Loading conversation..." />
            ) : messages.length === 0 ? (
              <Box sx={{ 
                flex: 1, 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 2,
              }}>
                <AiIcon sx={{ fontSize: 64, color: 'text.secondary' }} />
                <Typography variant="h6" color="text.secondary">
                  Start a conversation
                </Typography>
                <Typography variant="body2" color="text.secondary" textAlign="center">
                  Ask me anything! I can help you with information from your documents,
                  answer questions, and assist with various tasks.
                </Typography>
              </Box>
            ) : (
              <Box
                ref={messagesContainerRef}
                sx={{ 
                  flex: 1,
                  overflow: 'auto',
                  px: 1,
                }}
              >
                <List sx={{ py: 1 }}>
                  {messages.map((message) => (
                    <ChatMessage
                      key={message.id}
                      message={message}
                      onCopy={handleCopyMessage}
                    />
                  ))}
                  {isSending && (
                    <ListItem sx={{ justifyContent: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CircularProgress size={16} />
                        <Typography variant="body2" color="text.secondary">
                          AI is thinking...
                        </Typography>
                      </Box>
                    </ListItem>
                  )}
                </List>
                <div ref={messagesEndRef} />
              </Box>
            )}

            {/* Message Input */}
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              {sendMessageMutation.error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  Failed to send message. Please try again.
                </Alert>
              )}
              
              <Stack direction="row" spacing={1} alignItems="flex-end">
                <TextField
                  fullWidth
                  multiline
                  maxRows={4}
                  placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isSending}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 3,
                    },
                  }}
                />
                <IconButton
                  color="primary"
                  onClick={handleSendMessage}
                  disabled={!messageInput.trim() || isSending}
                  sx={{
                    bgcolor: 'primary.main',
                    color: 'white',
                    '&:hover': {
                      bgcolor: 'primary.dark',
                    },
                    '&:disabled': {
                      bgcolor: 'grey.300',
                    },
                  }}
                >
                  {isSending ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
                </IconButton>
              </Stack>
            </Box>
          </Paper>
        </Box>

        {/* Settings Sidebar */}
        <Box sx={{ width: 300 }}>
          <ChatSettings
            useRag={useRag}
            onUseRagChange={setUseRag}
            selectedProfile={selectedProfile}
            onProfileChange={setSelectedProfile}
            selectedPrompt={selectedPrompt}
            onPromptChange={setSelectedPrompt}
            profiles={profiles}
            prompts={prompts}
            expanded={settingsExpanded}
            onExpandedChange={setSettingsExpanded}
          />
        </Box>
      </Box>

      {/* Delete Conversation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Conversation"
        message="Are you sure you want to delete this conversation? This action cannot be undone."
        confirmText="Delete"
        confirmColor="error"
        loading={deleteConversationMutation.isPending}
        onConfirm={handleDeleteConversation}
        onCancel={() => setDeleteDialogOpen(false)}
      />
    </Box>
  );
}