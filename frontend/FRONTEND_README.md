# AI Chatbot Frontend

A comprehensive React TypeScript frontend for the AI Chatbot platform, providing an advanced interface for LLM experimentation, RAG document processing, and MCP tool integration.

## 🚀 Features

### Core Functionality
- **🔐 Authentication**: Complete user authentication with JWT token management
- **💬 Real-time Chat**: Advanced chatbot interface with conversation management
- **📄 Document Management**: Upload, process, and manage documents with RAG integration
- **🔍 Advanced Search**: Multiple search algorithms (vector, text, hybrid, MMR)
- **📊 Analytics Dashboard**: Interactive charts and visualizations using Chart.js
- **🎛️ LLM Profiles**: Parameter tuning for different conversation modes
- **📝 Prompt Templates**: Manage and organize AI prompts with categorization
- **🛠️ MCP Tools**: Manage Model Context Protocol servers and tools
- **⚙️ Settings**: User preferences, security, and account management

### Technical Highlights
- **TypeScript**: Full type safety with comprehensive API interfaces
- **Material-UI v5**: Modern, responsive design system
- **React Query**: Efficient server state management with caching
- **Chart.js**: Interactive data visualizations
- **Error Boundaries**: Graceful error handling throughout the app
- **Lazy Loading**: Optimized performance with code splitting
- **Responsive Design**: Mobile-friendly interface

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── auth/            # Authentication forms
│   │   ├── chat/            # Chat-related components
│   │   ├── common/          # Shared components
│   │   └── AppRouter.tsx    # Main routing configuration
│   ├── contexts/            # React contexts
│   │   └── AuthContext.tsx  # Authentication state management
│   ├── hooks/               # Custom React hooks
│   │   └── api.ts          # React Query hooks for API calls
│   ├── pages/               # Page components
│   │   ├── admin/          # Admin-only pages
│   │   ├── ChatPage.tsx    # Main chat interface
│   │   ├── DashboardPage.tsx # System overview
│   │   ├── DocumentsPage.tsx # Document management
│   │   ├── AnalyticsPage.tsx # Charts and analytics
│   │   └── ...             # Other main pages
│   ├── services/            # API service layer
│   │   └── api.ts          # HTTP client and API methods
│   ├── types/               # TypeScript type definitions
│   │   └── api.ts          # Complete API type definitions
│   ├── utils/               # Utility functions
│   ├── App.tsx             # Main application component
│   └── index.tsx           # Application entry point
├── public/                  # Static assets
├── package.json            # Dependencies and scripts
└── tsconfig.json           # TypeScript configuration
```

## 🛠️ Setup and Installation

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Running AI Chatbot backend API

### Installation Steps

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   Create a `.env` file in the frontend directory:
   ```env
   REACT_APP_API_URL=http://localhost:8000
   ```

4. **Start development server**:
   ```bash
   npm start
   ```

5. **Access the application**:
   Open http://localhost:3000 in your browser

### Production Build

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## 🎯 Key Components

### Authentication System
- **LoginForm**: User authentication with validation
- **RegisterForm**: New user registration
- **AuthContext**: Global authentication state management
- **Protected Routes**: Automatic redirect for unauthenticated users

### Chat Interface (`ChatPage.tsx`)
- Real-time messaging with AI assistant
- Conversation history and management
- RAG toggle for document-aware responses
- LLM profile and prompt selection
- Message copying and export functionality
- Token usage tracking and display

### Document Management (`DocumentsPage.tsx`)
- Drag-and-drop file upload
- Multi-format support (PDF, DOCX, TXT, MD, RTF)
- Processing status tracking with progress bars
- Document search and filtering
- Bulk operations and management

### Search Interface (`SearchPage.tsx`)
- Multiple search algorithms:
  - **Vector Search**: Semantic similarity using embeddings
  - **Text Search**: Traditional keyword-based search
  - **Hybrid Search**: Combines vector and text search
  - **MMR Search**: Maximum Marginal Relevance for diverse results
- Advanced filtering and result visualization
- Search suggestions and auto-completion

### Analytics Dashboard (`AnalyticsPage.tsx`)
- Interactive charts using Chart.js:
  - Usage trends over time
  - Token consumption patterns
  - Performance metrics
  - User activity distribution
- Exportable reports and data visualization
- Real-time and historical data analysis

### LLM Profiles (`ProfilesPage.tsx`)
- Parameter tuning interface:
  - Temperature (creativity control)
  - Max tokens (response length)
  - Top-p (nucleus sampling)
  - Frequency/presence penalties
- Profile creation and management
- Usage statistics and analytics

### Prompt Management (`PromptsPage.tsx`)
- Template creation and editing
- Category-based organization
- Tag system for easy discovery
- Usage tracking and statistics
- Default prompt management

### MCP Tools (`ToolsPage.tsx`)
- Server registration and management
- Tool enable/disable controls
- Usage statistics and performance metrics
- Connection status monitoring

## 🔧 API Integration

The frontend includes a comprehensive API service layer (`services/api.ts`) that provides:

### Features
- **Automatic Authentication**: JWT token management with automatic refresh
- **Error Handling**: Consistent error handling with user-friendly messages
- **Request Interceptors**: Automatic token attachment and request logging
- **Response Caching**: Intelligent caching with React Query
- **Type Safety**: Full TypeScript integration with backend APIs

### API Coverage
All backend endpoints are fully integrated:
- Authentication and user management
- Real-time chat with RAG capabilities
- Document upload and processing
- Advanced search functionality
- Analytics and reporting
- LLM profile management
- Prompt template operations
- MCP tool integration
- Administrative functions

## 📊 State Management

### React Query (TanStack Query)
Used for server state management with features:
- **Automatic Caching**: Reduces unnecessary API calls
- **Background Refetching**: Keeps data fresh automatically
- **Optimistic Updates**: Immediate UI updates for better UX
- **Error Recovery**: Automatic retry logic with exponential backoff
- **Pagination Support**: Efficient handling of large datasets

### React Context
Used for application state:
- **AuthContext**: User authentication and authorization
- **Theme Management**: UI customization and preferences

## 🎨 UI/UX Design

### Material-UI v5
- **Consistent Design**: Unified design system throughout the app
- **Responsive Layout**: Mobile-first design approach
- **Accessibility**: ARIA labels and keyboard navigation
- **Theming**: Customizable color schemes and typography

### Key Design Patterns
- **Progressive Disclosure**: Advanced features hidden behind accordions
- **Status Indicators**: Clear visual feedback for all operations
- **Loading States**: Skeleton screens and progress indicators
- **Error Handling**: User-friendly error messages with recovery actions

## 📚 TypeScript Guide for Beginners

Since you mentioned not knowing TypeScript, here's a practical guide:

### What is TypeScript?
TypeScript is JavaScript with type annotations. It helps catch errors before runtime and provides better development experience.

### Key Concepts in This Project

#### 1. Interfaces (Type Definitions)
```typescript
// Defines the shape of a User object
interface User {
  id: string;           // Required field
  name: string;         // Required field
  email?: string;       // Optional field (note the ?)
}
```

#### 2. Function Components
```typescript
// A React component with typed props
interface ButtonProps {
  label: string;
  onClick: () => void;
}

const Button: React.FC<ButtonProps> = ({ label, onClick }) => {
  return <button onClick={onClick}>{label}</button>;
};
```

#### 3. State with Types
```typescript
// State with explicit type
const [user, setUser] = useState<User | null>(null);

// Array state
const [messages, setMessages] = useState<Message[]>([]);
```

#### 4. API Responses
```typescript
// API function with return type
const fetchUser = async (id: string): Promise<User> => {
  const response = await api.get(`/users/${id}`);
  return response.data;
};
```

### Benefits You'll Notice
- **IntelliSense**: Auto-completion when typing
- **Error Prevention**: Catches typos and wrong types
- **Refactoring Safety**: Rename variables/functions safely
- **Documentation**: Types serve as documentation

### Learning Tips
1. **Start Small**: Focus on understanding one file at a time
2. **Use IDE**: VS Code provides excellent TypeScript support
3. **Read Error Messages**: TypeScript errors are usually helpful
4. **Don't Fight It**: If TypeScript complains, there's usually a good reason

## 🚀 Getting Started (For TypeScript Beginners)

### 1. Start the Development Server
```bash
cd frontend
npm install
npm start
```

### 2. Explore the Code
Start with these files to understand the structure:
- `src/App.tsx` - Main application setup
- `src/pages/DashboardPage.tsx` - Simple page example
- `src/components/auth/AuthComponents.tsx` - Form components
- `src/types/api.ts` - All type definitions

### 3. Make Small Changes
Try modifying:
- Text content in components
- Colors in the theme (App.tsx)
- Add new fields to forms

### 4. Understand Common Patterns
- **Props**: How data passes between components
- **State**: How components store and update data
- **Hooks**: How components interact with APIs
- **Types**: How TypeScript ensures correctness

## 🔧 Customization

### Adding New Features
1. **Add Types**: Define data structures in `types/api.ts`
2. **Add API Methods**: Create service functions in `services/api.ts`
3. **Add Hooks**: Create React Query hooks in `hooks/api.ts`
4. **Add Components**: Build UI components with TypeScript props
5. **Add Pages**: Create page components and add to router

### Styling Customization
The app uses Material-UI for styling. You can customize:
- **Colors**: Modify theme in `App.tsx`
- **Components**: Override Material-UI component styles
- **Layout**: Adjust spacing and sizing using Material-UI system

## 🐛 Troubleshooting

### TypeScript Errors
- **Red squiggly lines**: Hover to see error message
- **Build fails**: Run `npm run build` to see all errors
- **Type mismatch**: Check that data types match expected interface

### Common Issues
1. **"Property does not exist"**: Check if property is optional (`?`)
2. **"Cannot read property of undefined"**: Add null checks
3. **"Type X is not assignable to type Y"**: Verify data structure matches interface

### Getting Help
- Check browser console for runtime errors
- Use React DevTools to inspect component state
- Use React Query DevTools to debug API calls
- TypeScript errors usually provide helpful guidance

## 📈 Next Steps

### For Learning TypeScript
1. **Practice**: Modify existing components
2. **Experiment**: Add new features to understand patterns
3. **Read Documentation**: Material-UI and React Query docs
4. **Ask Questions**: TypeScript community is very helpful

### For Extending the App
1. **Add New Pages**: Follow existing page patterns
2. **Create Custom Components**: Build reusable UI elements
3. **Integrate New APIs**: Add backend endpoints
4. **Improve UX**: Add animations and transitions

---

This frontend provides a complete foundation for the AI Chatbot platform. The TypeScript annotations and extensive comments throughout the codebase will help you understand and extend the application even without prior TypeScript experience.