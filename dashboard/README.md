# AI Chatbot Dashboard

A full-featured React-based dashboard for the AI Chatbot Platform with separate areas for admins and users.

## Features

### User Features
- **Interactive Chat Interface** with streaming responses
- **Personal Dashboard** with activity charts and statistics
- **Real-time Message Streaming** using Server-Sent Events
- **Document Context** display in chat responses
- **Tool Call** indicators and summaries

### Admin Features
- **System Monitoring Dashboard** with comprehensive charts
- **User Management** interface
- **Document Processing** statistics
- **Usage Analytics** with ReCharts visualizations
- **System Health** monitoring

### Technical Features
- **Material-UI** components for consistent design
- **ReCharts** for interactive data visualizations
- **React Query** for efficient data fetching
- **React Router** for navigation
- **Responsive Design** for mobile and desktop
- **JWT Authentication** integration

## Installation

```bash
cd dashboard
npm install
npm start
```

The application will start on `http://localhost:3000` and proxy API requests to `http://localhost:8000`.

## Project Structure

```
dashboard/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   └── Sidebar.js
│   ├── pages/
│   │   ├── Login.js
│   │   ├── ChatInterface.js
│   │   ├── UserDashboard.js
│   │   └── AdminDashboard.js
│   ├── services/
│   │   └── AuthContext.js
│   ├── App.js
│   └── index.js
└── package.json
```

## Environment Variables

Create a `.env` file in the dashboard directory:

```
REACT_APP_API_URL=http://localhost:8000
```

## API Integration

The dashboard integrates with the following API endpoints:

- `POST /auth/login` - User authentication
- `GET /auth/me` - Get current user info
- `POST /conversations/chat` - Send chat messages
- `POST /conversations/chat/stream` - Streaming chat responses
- `GET /conversations/` - List conversations
- Admin endpoints for analytics and management

## Charts and Analytics

Uses ReCharts library for:
- Line charts for usage trends
- Bar charts for activity patterns
- Pie charts for data distribution
- Area charts for document processing
- Real-time data updates

## Streaming Chat

Implements Server-Sent Events for real-time streaming:
- Progressive message rendering
- Tool call indicators
- RAG context display
- Typing indicators
- Error handling with fallback to non-streaming

## Responsive Design

Fully responsive layout that adapts to:
- Desktop computers
- Tablets
- Mobile phones
- Collapsible sidebar
- Mobile-first design approach